#!/usr/bin/env python3

from __future__ import annotations

import collections.abc
import logging
import pandas as pd
from pandas import DataFrame
import dask
from dask.distributed import LocalCluster, Client, as_completed, Future
from google.oauth2 import service_account
import sqlalchemy as sa
from EMS.manager import Databases, get_gbq_credentials

from vizier.service import clients
from vizier.service import pyvizier as vz

logger = logging.getLogger(__name__)


class EvalOnCluster(object):

    def __init__(self, client: Client,
                 table_name: str, credentials: service_account.credentials = None):
        self.db = Databases(table_name, None, credentials, None)
        self.client = client
        self.credentials = credentials
        self.experiment = None  # Iterable returning (future, df).
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
        future = self.client.submit(instance, **params)
        if self.experiment is None:
            self.experiment = as_completed([future], with_results=True)
        else:
            self.experiment.add(future)
        return tuple(params[k] for k in self.keys)

    def result(self) -> (DataFrame, tuple):  # Return a DataFrame and a key.
        future, result = next(self.experiment)
        self.db.push(result)
        future.release()  # EP function; release the data; will not be reused.
        values = result[self.keys].to_numpy()
        yield result, tuple(v for v in values[0])

    def final_push(self):
        self.db.final_push()
        self.client.shutdown()


# Objective function to maximize.
def experiment(*, w: float, x: int, y: float, z: str) -> DataFrame:
    objective = w**2 - y**2 + x * ord(z)
    return DataFrame(data={'w': w, 'x': x, 'y': y, 'z': z, 'objective': objective}, index=[0])


def get_vizier_study(owner: str = 'my_name', study_id: str = 'example') -> clients.Study:
    # Algorithm, search space, and metrics.
    study_config = vz.StudyConfig(algorithm='GAUSSIAN_PROCESS_BANDIT')

    study_config.search_space.root.add_float_param('w', 0.0, 5.0)
    study_config.search_space.root.add_int_param('x', -2, 2)
    study_config.search_space.root.add_discrete_param('y', [0.3, 7.2])
    study_config.search_space.root.add_categorical_param('z', ['a', 'g', 'k'])
    study_config.metric_information.append(vz.MetricInformation('metric_name', goal=vz.ObjectiveMetricGoal.MAXIMIZE))

    return clients.Study.from_study_config(study_config, owner=owner, study_id=study_id)


def setup_vizier():
    study = get_vizier_study('adonoho', 'test_01')

    for i in range(100):
        suggestions = study.suggest(count=1)
        for suggestion in suggestions:
            params = suggestion.parameters
            df = experiment(**params)
            suggestion.complete(vz.Measurement({'metric_name': df.iloc[0]['objective']}))


def setup_vizier_on_local_cluster():
    study = get_vizier_study('adonoho', 'test_cluster_01')

    with LocalCluster() as cluster:
        with Client(cluster) as client:
            ec = EvalOnCluster(client, None)
            # ec = EvalOnCluster(client, 'test_cluster_01')
            in_cluster = {}
            for suggestion in study.suggest(count=1):
                params = suggestion.parameters
                key = ec.eval_params(experiment, dict(params))
                in_cluster[key] = suggestion
            for df, key in ec.result():
                suggestion = in_cluster[key]
                suggestion.complete(vz.Measurement({'metric_name': df.iloc[0]['objective']}))
                del in_cluster[key]
            ec.final_push()


if __name__ == "__main__":
    # setup_vizier()
    setup_vizier_on_local_cluster()
