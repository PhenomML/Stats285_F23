#!/usr/bin/env python3

import logging
import pandas as pd
from pandas import DataFrame
import dask
import dask.dataframe as dd
from dask.distributed import LocalCluster, Client, worker_client, as_completed, Future
from google.cloud import bigquery
from google.oauth2 import service_account
import sqlalchemy as sa
from EMS.manager import Databases, get_gbq_credentials

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


TABLE_NAMES = {  # URL to GBQ table name map.
    """
    Let’s do these four datasets:
    1) Adult Income: https://archive.ics.uci.edu/dataset/2/adult
    2) California housing: https://www.kaggle.com/datasets/camnugent/california-housing-prices
    3) Forest Covertype: https://archive.ics.uci.edu/dataset/31/covertype
    4) Higgs: https://www.kaggle.com/c/higgs-boson
    """
    'https://archive.ics.uci.edu/dataset/2/adult': 'XYZ.adult_income',
    'https://www.kaggle.com/datasets/camnugent/california-housing-prices': 'XYZ.california_housing_prices',
    'https://archive.ics.uci.edu/dataset/31/covertype': 'XYZ.forest_covertype',
    'https://www.kaggle.com/c/higgs-boson/training': 'XYZ.higgs_boson_training',
    'https://www.kaggle.com/c/higgs-boson/test': 'XYZ.higgs_boson_test',
}

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


def experiment(*, key: str) -> DataFrame:
    df = get_dataset(key)
    if df is not None:
        logger.info(f'{df}')
    else:
        logger.info('Missing Data!')
    return DataFrame(data={'key': key, 'transfer_succeeded': df is not None}, index=[0])


def get_df_from_gbq(table_name, credentials: service_account.credentials = None):
    client = bigquery.Client(credentials=credentials)
    query = f"SELECT * FROM `{table_name}`"
    df = client.query(query).to_dataframe()
    return df


def push_tables_to_cluster(tables: dict, c: Client, credentials: service_account.credentials = None):
    for key, table in tables.items():
        df = get_df_from_gbq(table, credentials)
        c.publish_dataset(df, name=key)
        logger.info(f'{key}\n{df}')


def push_to_dataset(c: Client) -> str:
    key = 'Kaggle.survey_2022_responses'
    df = get_df_from_gbq(key)
    c.publish_dataset(df, name=key)
    return key


def setup_dataset(credentials: service_account.credentials = None):
    with LocalCluster() as l, Client(l) as lc:
        ec = EvalOnCluster(lc, None)
        push_tables_to_cluster(TABLE_NAMES, lc, credentials)
        logger.info(f'{lc.list_datasets()}')
        for url, table in TABLE_NAMES.items():
            params = {'key': url}
            key = ec.eval_params(experiment, params)
            df, key = next(ec.result())
            logger.info(f'{key}\n{df}')


if __name__ == "__main__":
    credentials = get_gbq_credentials('stanford-stats-285-donoho-0dc233389eb9.json')
    setup_dataset(credentials)
