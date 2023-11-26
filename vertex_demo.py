#!/usr/bin/env python3

import logging
import pandas as pd
from pandas import DataFrame
from dask.distributed import LocalCluster, Client, worker_client, as_completed
from google.oauth2 import service_account
from EMS.manager import Databases, get_gbq_credentials

from google.cloud import aiplatform
from google.cloud.aiplatform.vizier import pyvizier as vz
from google.cloud.aiplatform.vizier import Study

logger = logging.getLogger(__name__)


class EvalOnCluster(object):

    def __init__(self, client: Client,
                 table_name: str, credentials: service_account.credentials = None):
        self.db = Databases(table_name, None, credentials, None)
        self.client = client
        self.credentials = credentials
        self.computations = None  # Iterable returning (future, df).
        self.keys = None

    def eval_params(self, instance: callable, params: dict) -> tuple:
        """
        Evaluate the instance with the params and return a tuple of param values that could become a key in a dict.
        :param instance: The `callable` to be invoked on the cluster.
        :param params: The `kwargs` to be passed to the `instance`
        :return: A tuple of param values suitable to become a key in a dict.
        """

        if self.keys is None:
            self.keys = sorted(params.keys())
        futures = self.client.map(lambda p: instance(**p), [params])  # To isolate kwargs, use a lambda function.
        if self.computations is None:
            self.computations = as_completed(futures, with_results=True)
        else:
            self.computations.update(futures)
        return tuple(params[k] for k in self.keys)

    def result(self) -> (DataFrame, tuple):  # Return a DataFrame and a key.
        future, result = next(self.computations)
        self.db.push(result)
        future.release()  # EP function; release the data; will not be reused.
        values = result[self.keys].to_numpy()
        yield result, tuple(v for v in values[0])

    def final_push(self):
        self.db.final_push()
        self.client.shutdown()


def on_worker() -> bool:
    import distributed.worker

    try:
        _ = distributed.worker.get_worker()
        return True
    except ValueError:
        return False


def get_dataset(key: str) -> DataFrame:
    if on_worker():
        with worker_client() as wc:
            df = wc.get_dataset(name=key, default=None)
    else:
        wc = Client.current(allow_global=True)
        df = wc.get_dataset(name=key, default=None)
    if df is not None:
        return df.copy(deep=True)  # Defend against mutating common data.
    return None


# Objective function to maximize.
def experiment_1(*, w: float, x: int, y: float, z: str) -> DataFrame:
    objective = w**2 - y**2 + x * ord(z)
    return DataFrame(data={'w': w, 'x': x, 'y': y, 'z': z, 'objective': objective}, index=[0])


def get_vertex_study(study_id: str = 'simple_example',
                     project: str = 'stanford-stats-285-donoho',
                     credentials: service_account.Credentials = None) -> Study:
    # Algorithm, search space, and metrics.
    study_config = vz.StudyConfig(algorithm=vz.Algorithm.RANDOM_SEARCH)  # Free on Vertex AI.
    # study_config = vz.StudyConfig(algorithm=vz.Algorithm.GAUSSIAN_PROCESS_BANDIT)

    study_config.search_space.root.add_float_param('w', 0.0, 5.0)
    study_config.search_space.root.add_int_param('x', -2, 2)
    study_config.search_space.root.add_discrete_param('y', [0.3, 7.2])
    study_config.search_space.root.add_categorical_param('z', ['a', 'g', 'k'])
    study_config.metric_information.append(vz.MetricInformation('metric_name', goal=vz.ObjectiveMetricGoal.MAXIMIZE))

    aiplatform.init(project=project, location='us-central1', credentials=credentials)
    study = Study.create_or_load(display_name=study_id, problem=study_config)
    return study


def setup_vertex(credentials: service_account.Credentials):
    study = get_vertex_study(study_id='test_local_01', credentials=credentials)

    suggestions = study.suggest(count=100)
    for suggestion in suggestions:
        params = suggestion.materialize().parameters.as_dict()
        params['x'] = round(params['x'])
        df = experiment_1(**params)
        measurement = vz.Measurement()
        measurement.metrics['metric_name'] = df.iloc[0]['objective']
        suggestion.add_measurement(measurement=measurement)
        suggestion.complete(measurement=measurement)
    optimal_trials = study.optimal_trials()
    logger.info(f'{optimal_trials}')


def setup_vertex_on_local_cluster_1(credentials: service_account.Credentials):
    study = get_vertex_study(study_id='test_cluster_01', credentials=credentials)

    with LocalCluster() as cluster:
        with Client(cluster) as client:
            ec = EvalOnCluster(client, None)
            # ec = EvalOnCluster(client, 'test_cluster_01')
            in_cluster = {}
            for _ in range(20):
                for suggestion in study.suggest(count=100):
                    params = suggestion.materialize().parameters.as_dict()
                    params['x'] = round(params['x'])
                    key = ec.eval_params(experiment_1, params)
                    in_cluster[key] = suggestion
                for df, key in ec.result():
                    measurement = vz.Measurement()
                    measurement.metrics['metric_name'] = df.iloc[0]['objective']
                    suggestion = in_cluster[key]
                    suggestion.add_measurement(measurement=measurement)
                    suggestion.complete(measurement=measurement)
                    del in_cluster[key]
            ec.final_push()
    optimal_trials = study.optimal_trials()
    logger.info(f'{optimal_trials}')


def setup_vizier_on_local_cluster_2():
    study = get_vertex_study(study_id='test_cluster_02')

    with LocalCluster() as cluster:
        with Client(cluster) as client:
            ec = EvalOnCluster(client, None)
            # ec = EvalOnCluster(client, 'test_cluster_01')
            in_cluster = {}
            for suggestion in study.suggest(count=1):
                params = suggestion.parameters
                key = ec.eval_params(experiment_1, dict(params))
                in_cluster[key] = suggestion
            for df, key in ec.result():
                suggestion = in_cluster[key]
                suggestion.complete(vz.Measurement({'metric_name': df.iloc[0]['objective']}))
                del in_cluster[key]
            ec.final_push()


if __name__ == "__main__":
    # setup_vertex(get_gbq_credentials('stanford-stats-285-donoho-vizier-b8a57b59c6d6.json'))
    setup_vertex_on_local_cluster_1(get_gbq_credentials('stanford-stats-285-donoho-vizier-b8a57b59c6d6.json'))
