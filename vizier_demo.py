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

    def eval_params(self, instance: callable, params: dict) -> Future:

        future = self.client.submit(instance, **params)
        if self.experiment is None:
            self.experiment = as_completed([future], with_results=True)
        else:
            self.experiment.add(future)

    def result(self) -> DataFrame:
        future, result = next(self.experiment)
        self.db.push(result)
        future.release()  # EP function; release the data; will not be reused.
        yield result

    def final_push(self):
        self.db.final_push()
        self.client.shutdown()


# Objective function to maximize.
def evaluate(*, w: float, x: int, y: float, z: str) -> DataFrame:
    objective =  w**2 - y**2 + x * ord(z)
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
            df = evaluate(**params)
            suggestion.complete(vz.Measurement({'metric_name': df.iloc[0]['objective']}))


def setup_vizier_on_local_cluster():
    study = get_vizier_study('adonoho', 'test_cluster_01')

    with LocalCluster() as cluster:
        with Client(cluster) as client:
            ec = EvalOnCluster(client, None)
            # ec = EvalOnCluster(client, 'test_cluster_01')
            for i in range(100):
                suggestions = study.suggest(count=1)
                for suggestion in suggestions:
                    params = suggestion.parameters
                    _ = ec.eval_params(evaluate, dict(params))
                    df = next(ec.result())
                    suggestion.complete(vz.Measurement({'metric_name': df.iloc[0]['objective']}))
            ec.final_push()


if __name__ == "__main__":
    # setup_vizier()
    setup_vizier_on_local_cluster()
