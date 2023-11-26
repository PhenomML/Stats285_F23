#!/usr/bin/env python3

import logging
import pandas as pd
from pandas import DataFrame
from dask.distributed import LocalCluster, Client
from google.cloud import bigquery
from google.oauth2 import service_account
from EMS.manager import EvalOnCluster, get_gbq_credentials, get_dataset

from google.cloud import aiplatform
from google.cloud.aiplatform.vizier import pyvizier as vz
from google.cloud.aiplatform.vizier import Study

logger = logging.getLogger(__name__)


"""
Let’s do these four datasets:
1) Adult Income: https://archive.ics.uci.edu/dataset/2/adult
2) California housing: https://www.kaggle.com/datasets/camnugent/california-housing-prices
3) Forest Covertype: https://archive.ics.uci.edu/dataset/31/covertype
4) Higgs: https://www.kaggle.com/c/higgs-boson
"""
class StudyURL:
    UCIML_ADULT_INCOME = 'https://archive.ics.uci.edu/dataset/2/adult'
    KAGGLE_CALIFORNIA_HOUSING_PRICES = 'https://www.kaggle.com/datasets/camnugent/california-housing-prices'
    UCIML_FOREST_COVERTYPE = 'https://archive.ics.uci.edu/dataset/31/covertype'
    KAGGLE_HIGGS_BOSON = 'https://www.kaggle.com/c/higgs-boson/'
    KAGGLE_HIGGS_BOSON_TRAINING = 'https://www.kaggle.com/c/higgs-boson/training'
    KAGGLE_HIGGS_BOSON_TEST = 'https://www.kaggle.com/c/higgs-boson/test'


TABLE_NAMES = {  # URL to GBQ table name map.
    StudyURL.UCIML_ADULT_INCOME: 'XYZ.adult_income',
    StudyURL.KAGGLE_CALIFORNIA_HOUSING_PRICES: 'XYZ.california_housing_prices',
    StudyURL.UCIML_FOREST_COVERTYPE: 'XYZ.forest_covertype',
    StudyURL.KAGGLE_HIGGS_BOSON_TRAINING: 'XYZ.higgs_boson_training',
    StudyURL.KAGGLE_HIGGS_BOSON_TEST: 'XYZ.higgs_boson_test',
}


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


# Objective functions to maximize.
def experiment_uciml_adult_income(*, url: str, df: DataFrame, **kwargs) -> DataFrame:
    return None


def experiment_kaggle_california_housing_prices(*, url: str, df: DataFrame, **kwargs) -> DataFrame:
    return None


def experiment_uciml_forest_covertype(*, url: str, df: DataFrame, **kwargs) -> DataFrame:
    return None


def experiment_kaggle_higgs_boson(*, url: str, df: DataFrame, **kwargs) -> DataFrame:
    return None


def experiment_local(*, url: str, df: DataFrame, **kwargs) -> DataFrame:
    match url:
        case StudyURL.UCIML_ADULT_INCOME:
            return experiment_uciml_adult_income(url=url, df=df, **kwargs)
        case StudyURL.KAGGLE_CALIFORNIA_HOUSING_PRICES:
            return experiment_kaggle_california_housing_prices(url=url, df=df, **kwargs)
        case StudyURL.UCIML_FOREST_COVERTYPE:
            return experiment_uciml_forest_covertype(url=url, df=df, **kwargs)
        case StudyURL.KAGGLE_HIGGS_BOSON_TRAINING | StudyURL.KAGGLE_HIGGS_BOSON_TEST:
            return experiment_kaggle_higgs_boson(url=url, df=df, **kwargs)
        case default:
            return None


def experiment(*, url: str, **kwargs) -> DataFrame:
    df = get_dataset(url)
    return experiment_local(url=url, df=df, **kwargs)


# def experiment_1(*, w: float, x: int, y: float, z: str) -> DataFrame:
#     objective = w**2 - y**2 + x * ord(z)
#     return DataFrame(data={'w': w, 'x': x, 'y': y, 'z': z, 'objective': objective}, index=[0])


def get_vertex_study(study_id: str = 'xyz_example',
                     project: str = 'stanford-stats-285-donoho',
                     credentials: service_account.Credentials = None) -> Study:
    # Algorithm, search space, and metrics.
    study_config = vz.StudyConfig(algorithm=vz.Algorithm.RANDOM_SEARCH)  # Free on Vertex AI.
    # study_config = vz.StudyConfig(algorithm=vz.Algorithm.GAUSSIAN_PROCESS_BANDIT)

    # study_config.search_space.root.add_float_param('w', 0.0, 5.0)
    # study_config.search_space.root.add_int_param('x', -2, 2)
    # study_config.search_space.root.add_discrete_param('y', [0.3, 7.2])
    study_config.search_space.root.add_categorical_param('url', [
        StudyURL.UCIML_ADULT_INCOME,
        StudyURL.KAGGLE_CALIFORNIA_HOUSING_PRICES,
        StudyURL.UCIML_FOREST_COVERTYPE,
        StudyURL.KAGGLE_HIGGS_BOSON_TRAINING
    ])
    study_config.metric_information.append(vz.MetricInformation('metric_name', goal=vz.ObjectiveMetricGoal.MAXIMIZE))

    aiplatform.init(project=project, location='us-central1', credentials=credentials)
    study = Study.create_or_load(display_name=study_id, problem=study_config)
    return study


def setup_xyz_vertex_on_local_cluster(credentials: service_account.Credentials):
    study = get_vertex_study(study_id='test_cluster_01', credentials=credentials)

    with LocalCluster() as cluster:
        with Client(cluster) as client:
            push_tables_to_cluster(TABLE_NAMES, client, credentials=credentials)
            ec = EvalOnCluster(client, None)
            # ec = EvalOnCluster(client, 'test_cluster_01')
            in_cluster = {}
            for _ in range(20):
                for suggestion in study.suggest(count=100):
                    params = suggestion.materialize().parameters.as_dict()
                    params['x'] = round(params['x'])
                    key = ec.eval_params(experiment, params)
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


def setup_experiment(url: str, credentials: service_account.Credentials):
    df = get_df_from_gbq(TABLE_NAMES[url], credentials=credentials)
    df_result = experiment_local(url=url, df=df, **{})
    logger.info(f'{url}\n{df}\n{df_result}')


if __name__ == "__main__":
    credentials = get_gbq_credentials('stanford-stats-285-donoho-vizier-b8a57b59c6d6.json')
    # setup_xyz_vertex_on_local_cluster(credentials=credentials)
    setup_experiment(StudyURL.UCIML_ADULT_INCOME, credentials=credentials)
    setup_experiment(StudyURL.KAGGLE_CALIFORNIA_HOUSING_PRICES, credentials=credentials)
    setup_experiment(StudyURL.UCIML_FOREST_COVERTYPE, credentials=credentials)
    setup_experiment(StudyURL.KAGGLE_HIGGS_BOSON_TRAINING, credentials=credentials)
