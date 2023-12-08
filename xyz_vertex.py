#!/usr/bin/env python3

import logging
from pathlib import Path
from tornado.ioloop import IOLoop
import numpy as np
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import xgboost as xgb
import catboost
import lightgbm as lgb
import pandas as pd
from pandas import DataFrame

from dask.distributed import LocalCluster, Client
from dask_jobqueue import SLURMCluster
from google.cloud import bigquery
from google.oauth2 import service_account
from EMS.manager import EvalOnCluster, get_gbq_credentials, get_dataset, do_on_cluster

from google.cloud import aiplatform
from google.cloud.aiplatform.vizier import pyvizier as vz
from google.cloud.aiplatform.vizier import Study

logging.basicConfig(level=logging.INFO)
# logging.basicConfig(level=logging.WARNING)
logging.getLogger('LightGBM').setLevel(logging.WARNING)
logger = logging.getLogger()


class StudyBOOST:
    XGBOOST = 'xgboost'
    CATBOOST = 'catboost'
    LIGHTGBM = 'lightgbm'


class StudyURL:
    """
    Let’s do these four datasets:
    1) Adult Income: https://archive.ics.uci.edu/dataset/2/adult
    2) California housing: https://www.kaggle.com/datasets/camnugent/california-housing-prices
    3) Forest Covertype: https://archive.ics.uci.edu/dataset/31/covertype
    4) Higgs: https://www.kaggle.com/c/higgs-boson
    """
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


def get_df_from_gbq(table_name, credentials: service_account.Credentials = None):
    client = bigquery.Client(credentials=credentials)
    query = f"SELECT * FROM `{table_name}`"
    df = client.query(query).to_dataframe()
    return df


def push_tables_to_cluster(tables: dict, c: Client, credentials: service_account.Credentials = None):
    for key, table in tables.items():
        df = get_df_from_gbq(table, credentials)
        c.publish_dataset(df, name=key)
        logger.info(f'{key}\n{df}')


def push_tables_to_filesystem(tables: dict, path: Path, credentials: service_account.Credentials = None):
    for key, table in tables.items():
        df = get_df_from_gbq(table, credentials)
        filename = table + '.parquet'
        p = path / filename
        df.to_parquet(path=p)
        logger.info(f'{key}\n{df}')


DATASETS = {}


def get_local_dataset(key: str) -> DataFrame:
    df = DATASETS.get(key, None)
    if df is None:
        df = get_dataset(key)
        DATASETS[key] = df
    return df.copy(deep=True)  # Defend against mutating common data.


# Objective functions to maximize.
def experiment_local(*, url: str, X_df: DataFrame, y_df: DataFrame, boost: str,
                     depth: int, reg_lambda: float, learning_rate: float, num_rounds: int) -> DataFrame:
    logger.warning(f'url: {url}; boost: {boost}\n{depth}, {reg_lambda}, {learning_rate}, {num_rounds}')
    # Create data array
    X = X_df.values

    # Convert y into target array
    y_array = y_df.iloc[:, 0].to_numpy()

    # Create target vector
    if np.issubdtype(y_array.dtype, np.number):
        y = y_array
        num_classes = 1
        obj_type = 'reg'
    else:
        # If y is categorical (including strings), use LabelEncoder for encoding
        encoder = LabelEncoder()
        y = encoder.fit_transform(y_array)
        num_classes = len(encoder.classes_)
        obj_type = 'bin' if num_classes == 2 else 'mult'

    # Split into train and test
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    match boost:
        case StudyBOOST.XGBOOST:
            xgb_params = {'learning_rate': learning_rate, 'reg_lambda': reg_lambda,
                          'max_depth': depth, 'n_estimators': num_rounds}
            match obj_type:
                case 'reg':
                    xgb_params['objective'] = 'reg:squarederror'
                case 'bin':
                    xgb_params['objective'] = 'binary:logistic'
                case 'mult':
                    xgb_params['objective'] = 'multi:softprob'
                    xgb_params['num_classes'] = num_classes
            model = xgb.XGBRegressor(**xgb_params) if obj_type == 'reg' else xgb.XGBClassifier(**xgb_params)
        case StudyBOOST.CATBOOST:
            model = catboost.CatBoostClassifier(learning_rate=learning_rate,
                                                l2_leaf_reg=reg_lambda,
                                                depth=depth,
                                                iterations=num_rounds,
                                                silent=True)
        case StudyBOOST.LIGHTGBM:
            model = lgb.LGBMClassifier(learning_rate=learning_rate,
                                       lambda_l2=reg_lambda,
                                       max_depth=depth,
                                       n_estimators=num_rounds,
                                       verbose=-1)
        case _:
            raise Exception("Invalid Method Name!")
    model.fit(X_train, y_train)

    # Make predictions on the test set
    test_preds = model.predict(X_test)
    test_predictions = [1 if x > 0.5 else 0 for x in test_preds]
    test_accuracy = accuracy_score(y_test, test_predictions)

    return DataFrame(data={'url': url, 'boost': boost, 'depth': depth,
                           'reg_lambda': reg_lambda, 'learning_rate': learning_rate, 'num_rounds': num_rounds,
                           'test_accuracy': test_accuracy},
                     index=[0])


def category_encode(df: DataFrame) -> DataFrame:
    # Select object columns
    object_cols = df.select_dtypes(include='object').columns

    # One-shot encode these columns
    df_encoded = pd.get_dummies(df, columns=object_cols)

    # Preview
    logger.info(f'{df_encoded.head()}')

    return df_encoded


def normalize_dataset(url: str, df: DataFrame) -> (DataFrame, DataFrame):
    match url:
        case StudyURL.UCIML_ADULT_INCOME:
            y_df = df[['income']]
            X_df = df.drop('income', axis=1)
        case StudyURL.KAGGLE_CALIFORNIA_HOUSING_PRICES:
            y_df = df[['median_house_value']]
            X_df = df.drop('median_house_value', axis=1)
        case StudyURL.UCIML_FOREST_COVERTYPE:
            y_df = df[['Cover_Type']]
            X_df = df.drop('Cover_Type', axis=1)
        case StudyURL.KAGGLE_HIGGS_BOSON_TRAINING | StudyURL.KAGGLE_HIGGS_BOSON_TEST:
            y_df = df[['Label']]
            X_df = df.drop('Label', axis=1)
        case _:
            raise Exception("Invalid Dataset Name!")
    X_df = category_encode(X_df)
    return X_df, y_df


def experiment(*, url: str, boost: str,
               depth: int, reg_lambda: float, learning_rate: float, num_rounds: int) -> DataFrame:
    df = get_local_dataset(url)
    df, y_df = normalize_dataset(url, df)
    return experiment_local(url=url, X_df=df, y_df=y_df, boost=boost,
                            depth=depth, reg_lambda=reg_lambda, learning_rate=learning_rate, num_rounds=num_rounds)


def get_vertex_study(study_id: str = 'xyz_example',
                     project: str = 'stanford-stats-285-donoho',
                     credentials: service_account.Credentials = None) -> Study:
    # Algorithm, search space, and metrics.
    # study_config = vz.StudyConfig(algorithm=vz.Algorithm.RANDOM_SEARCH)  # Free on Vertex AI.
    study_config = vz.StudyConfig(algorithm=vz.Algorithm.ALGORITHM_UNSPECIFIED)

    root = study_config.search_space.select_root()
    root.add_float_param('reg_lambda', 0.25, 4.0)
    root.add_float_param('learning_rate', 0.1, 1.0)
    root.add_discrete_param('depth', [6, 8, 10])
    root.add_discrete_param('num_rounds', [50])
    root.add_categorical_param('url', [
        StudyURL.UCIML_ADULT_INCOME,
        StudyURL.KAGGLE_CALIFORNIA_HOUSING_PRICES,
        StudyURL.UCIML_FOREST_COVERTYPE,
        StudyURL.KAGGLE_HIGGS_BOSON_TRAINING
    ])
    root.add_categorical_param('boost', [
        StudyBOOST.XGBOOST,
        # StudyBOOST.CATBOOST,
        StudyBOOST.LIGHTGBM
    ])
    study_config.metric_information.append(vz.MetricInformation('test_accuracy', goal=vz.ObjectiveMetricGoal.MAXIMIZE))

    aiplatform.init(project=project, location='us-central1', credentials=credentials)
    study = Study.create_or_load(display_name=study_id, problem=study_config)
    return study


def calc_xyz_vertex_on_cluster(table_name: str, client: Client, nodes: int, credentials: service_account.Credentials):

    # MAX_NUM_ITERATIONS = 360  # Same number as the EMS version.
    MAX_NUM_ITERATIONS = 6 * 10  # Sagi Perel suggestion. Less than the 360 used in EMS example.
    study = get_vertex_study(study_id=table_name, credentials=credentials)
    ec = EvalOnCluster(client, table_name)
    in_cluster = {}

    def push_suggestions_to_cluster(count):
        for suggestion in study.suggest(count=count):
            params = suggestion.materialize().parameters.as_dict()
            params['depth'] = round(params['depth'])
            params['num_rounds'] = round(params['num_rounds'])
            key = ec.eval_params(experiment, params)
            in_cluster[key] = suggestion
        logger.info(f'Pending computations: {len(in_cluster)}.')

    def push_result_to_vertex(df: DataFrame, key: tuple):
        measurement = vz.Measurement()
        measurement.metrics['test_accuracy'] = df.iloc[0]['test_accuracy']
        suggestion = in_cluster[key]
        suggestion.add_measurement(measurement=measurement)
        suggestion.complete(measurement=measurement)
        del in_cluster[key]

    # Prime the cluster.
    push_suggestions_to_cluster(8)  # Each node has 2 threads, keeps cluster busy.
    # push_suggestions_to_cluster(3 * nodes)  # Each node has 2 threads, keeps cluster busy.
    i = 0
    for df, key in ec.result():  # Start retiring trials.
        logger.info(f'Result: {df}.')
        push_result_to_vertex(df, key)
        i += 1
        logger.info(f'Completed computations: {i}; Pending: {len(in_cluster)}.')
        if i + len(in_cluster) <= MAX_NUM_ITERATIONS:
            push_suggestions_to_cluster(1)
    ec.final_push()
    optimal_trials = study.optimal_trials()
    logger.info(f'{optimal_trials}')


async def calc_xyz_vertex_on_cluster_async(table_name: str, client: Client,
                                           nodes: int, credentials: service_account.Credentials):

    MAX_NUM_ITERATIONS = 6 * 10  # Sagi Perel suggestion. Less than the 360 used in EMS example.
    study = get_vertex_study(study_id=table_name, credentials=credentials)
    ec = EvalOnCluster(client, table_name, credentials=credentials)
    in_cluster = {}

    def push_suggestions_to_cluster(count):
        logger.info(f'Call Vizier.')
        for suggestion in study.suggest(count=count):
            params = suggestion.materialize().parameters.as_dict()
            params['depth'] = round(params['depth'])
            params['num_rounds'] = round(params['num_rounds'])
            key = ec.key_from_params(params)
            if not in_cluster.get(key, None):  # Defend against duplicate computation.
                logger.info(f'EC Key: {key}\nParams: {params}')
                key = ec.eval_params(experiment, params)
                in_cluster[key] = suggestion
        logger.info(f'Pending computations: {len(in_cluster)}.')

    def push_result_to_vertex(df: DataFrame, key: tuple):
        logger.info(f'Push result to Vizier, EC Key: {key}')
        measurement = vz.Measurement()
        measurement.metrics['test_accuracy'] = df.iloc[0]['test_accuracy']
        suggestion = in_cluster.get(key, None)
        if suggestion is not None:
            suggestion.add_measurement(measurement=measurement)
            suggestion.complete(measurement=measurement)
            del in_cluster[key]
        else:
            logger.info(f'Key problem: {key}\n{in_cluster}')
        logger.info(f'End Push.')

    # Prime the cluster.
    push_suggestions_to_cluster(2 * nodes)
    i = 0
    for df, key in ec:  # Start retiring trials.
        logger.info(f'Result: {df}.')
        # push_result_to_vertex(df, key)
        await IOLoop.current().run_in_executor(None, push_result_to_vertex, df, key)
        i += 1
        active_suggestions = len(in_cluster)
        logger.info(f'Completed computations: {i}; Pending: {active_suggestions}.')
        if i <= MAX_NUM_ITERATIONS:
            # push_suggestions_to_cluster(2 * nodes)
            await IOLoop.current().run_in_executor(None, push_suggestions_to_cluster, 2 * nodes)
        elif i >= MAX_NUM_ITERATIONS:
            logger.info(f'Unclaimed suggestions:\n{in_cluster}')
            break
    logger.info('Finishing')
    ec.final_push()
    optimal_trials = study.optimal_trials()
    logger.info(f'{optimal_trials}')


def setup_xyz_vertex_on_local_node(table_name: str, credentials: service_account.Credentials):
    with LocalCluster() as lc, Client(lc) as client:
        logger.info(f'Local cluster: {lc}, Client: {client}')
        push_tables_to_cluster(TABLE_NAMES, client, credentials=credentials)
        nthreads = sum(w.nthreads for w in lc.workers.values())
        calc_xyz_vertex_on_cluster(table_name, client, nthreads, credentials)


async def setup_xyz_vertex_on_local_node_async(table_name: str, credentials: service_account.Credentials):
    lc = LocalCluster(n_workers=16, threads_per_worker=1)
    # lc = LocalCluster(n_workers=1, threads_per_worker=2)
    client = await Client(lc, asynchronous=True)
    logger.info(f'Local cluster: {lc}, Client: {client}')
    push_tables_to_cluster(TABLE_NAMES, client, credentials=credentials)
    nthreads = sum(w.nthreads for w in lc.workers.values())
    await calc_xyz_vertex_on_cluster_async(table_name, client, nthreads, credentials)
    client.close()
    await lc.close()


def setup_xyz_vertex_on_cluster(table_name: str, credentials: service_account.Credentials):
    nodes = 8
    with SLURMCluster(cores=1, memory='4GiB', processes=1, walltime='24:00:00') as cluster:
        cluster.scale(jobs=nodes)
        logging.info(cluster.job_script())
        with Client(cluster) as client:
            push_tables_to_cluster(TABLE_NAMES, client, credentials=credentials)
            calc_xyz_vertex_on_cluster(table_name, client, nodes, credentials)
        cluster.scale(0)


async def setup_xyz_vertex_on_cluster_async(table_name: str, credentials: service_account.Credentials):
    nodes = 8
    cluster = SLURMCluster(cores=1, memory='4GiB', processes=1, walltime='24:00:00')
    cluster.scale(jobs=nodes)
    logging.info(cluster.job_script())
    client = await Client(cluster, asynchronous=True)
    push_tables_to_cluster(TABLE_NAMES, client, credentials=credentials)
    await calc_xyz_vertex_on_cluster_async(table_name, client, nodes, credentials)
    client.close()
    cluster.scale(0)
    await cluster.close()


def create_config(su_id: str = 'su_id') -> dict:
    ems_spec = {
        'params': [{
            'depth': [6, 8, 10],
            'reg_lambda': [0.25, 0.5, 1., 2., 4.],
            'boost': [StudyBOOST.XGBOOST, StudyBOOST.LIGHTGBM],
            # 'boost': [StudyBOOST.XGBOOST, StudyBOOST.CATBOOST, StudyBOOST.LIGHTGBM],
            'url': [
                StudyURL.UCIML_ADULT_INCOME,
                StudyURL.KAGGLE_CALIFORNIA_HOUSING_PRICES,
                StudyURL.UCIML_FOREST_COVERTYPE,
                StudyURL.KAGGLE_HIGGS_BOSON_TRAINING
            ],
            'learning_rate': [0.1, 0.5, 1.],
            'num_rounds': [50]
        }],
        'param_types': {
            'depth': 'int',
            'reg_lambda': 'float',
            'boost': 'str',
            'url': 'str',
            'learning_rate': 'float',
            'num_rounds': 'int'
        },
        'table_name': f'XYZ_{su_id}',
        'GCP_project_id': 'stanford-stats-285-donoho',
        'description': 'Describe what this experiment does for future reference.'
    }
    return ems_spec


def setup_experiment(url: str, boost: str, depth: int, reg_lambda: float, learning_rate: float, num_rounds: int,
                     credentials: service_account.Credentials):
    df = get_df_from_gbq(TABLE_NAMES[url], credentials=credentials)
    df, y_df = normalize_dataset(url, df)
    df_result = experiment_local(url=url, X_df=df, y_df=y_df, boost=boost,
                                 depth=depth, reg_lambda=reg_lambda, learning_rate=learning_rate, num_rounds=num_rounds)
    logger.info(f'{url} by {boost}\n{df_result}')


def do_cluster_experiment(su_id: str = 'su_ID', credentials=None):
    exp = create_config(su_id=su_id)
    nodes = 8
    with SLURMCluster(cores=1, memory='4GiB', processes=1, walltime='24:00:00') as cluster:
        cluster.scale(jobs=nodes)
        logging.info(cluster.job_script())
        with Client(cluster) as client:
            push_tables_to_cluster(TABLE_NAMES, client, credentials=credentials)
            do_on_cluster(exp, experiment, client, credentials=credentials)
        cluster.scale(0)


def do_local_experiment(su_id: str = 'su_ID', credentials=None):
    exp = create_config(su_id=su_id)
    with LocalCluster() as lc, Client(lc) as client:
        push_tables_to_cluster(TABLE_NAMES, client, credentials=credentials)
        do_on_cluster(exp, experiment, client, credentials=credentials)


def do_vertex_on_local_async(table_name: str, credentials=None):
    async def run_it():
        await setup_xyz_vertex_on_local_node_async(table_name, credentials=credentials)

    IOLoop().run_sync(run_it)


def do_vertex_on_cluster_async(table_name: str, credentials=None):
    async def run_it():
        await setup_xyz_vertex_on_cluster_async(table_name, credentials=credentials)

    IOLoop().run_sync(run_it)


if __name__ == "__main__":
    su_id = 'adonoho'
    credentials = get_gbq_credentials('stanford-stats-285-donoho-0dc233389eb9.json')
    do_vertex_on_local_async(f'XYZ_{su_id}_test_06', credentials=credentials)
    # do_vertex_on_cluster_async(f'XYZ_{su_id}_test_05', credentials=credentials)
    # setup_xyz_vertex_on_local_node(f'XYZ_{su_id}_test_03', credentials=credentials)
    # setup_xyz_vertex_on_cluster(f'XYZ_{su_id}_vertex_test_01', credentials=credentials)
    # do_local_experiment('adonoho_test_01', credentials=credentials)
    # setup_experiment(StudyURL.UCIML_ADULT_INCOME, StudyBOOST.XGBOOST, 6, 0.25, 0.1, credentials=credentials)
    # setup_experiment(StudyURL.UCIML_ADULT_INCOME, StudyBOOST.CATBOOST, 6, 0.25, 0.1, credentials=credentials)
    # setup_experiment(StudyURL.UCIML_ADULT_INCOME, StudyBOOST.LIGHTGBM, 6, 0.25, 0.1, credentials=credentials)
    # setup_experiment(StudyURL.KAGGLE_CALIFORNIA_HOUSING_PRICES, StudyBOOST.XGBOOST, 6, 0.25, 0.1, credentials=credentials)
    # setup_experiment(StudyURL.KAGGLE_CALIFORNIA_HOUSING_PRICES, StudyBOOST.CATBOOST, 6, 0.25, 0.1, credentials=credentials)
    # setup_experiment(StudyURL.KAGGLE_CALIFORNIA_HOUSING_PRICES, StudyBOOST.LIGHTGBM, 6, 0.25, 0.1, credentials=credentials)
    # setup_experiment(StudyURL.UCIML_FOREST_COVERTYPE, StudyBOOST.XGBOOST, 6, 0.25, 0.1, credentials=credentials)
    # setup_experiment(StudyURL.UCIML_FOREST_COVERTYPE, StudyBOOST.CATBOOST, 6, 0.25, 0.1, credentials=credentials)
    # setup_experiment(StudyURL.UCIML_FOREST_COVERTYPE, StudyBOOST.LIGHTGBM, 6, 0.25, 0.1, credentials=credentials)
    # setup_experiment(StudyURL.KAGGLE_HIGGS_BOSON_TRAINING, StudyBOOST.XGBOOST, 6, 0.25, 0.1, credentials=credentials)
    # setup_experiment(StudyURL.KAGGLE_HIGGS_BOSON_TRAINING, StudyBOOST.CATBOOST, 6, 0.25, 0.1, credentials=credentials)
    # setup_experiment(StudyURL.KAGGLE_HIGGS_BOSON_TRAINING, StudyBOOST.LIGHTGBM, 6, 0.25, 0.1, credentials=credentials)
