#!/usr/bin/env python3

import time
import numpy as np
import pandas as pd
from pandas import DataFrame
from dask.distributed import Client, LocalCluster
from dask_jobqueue import SLURMCluster
from EMS.manager import do_on_cluster, get_gbq_credentials
import logging

logging.basicConfig(level=logging.INFO)

# Function that generates data with noise; will use again in later homeworks
def generate_data(nrow: int, ncol: int, seed: int = 0) -> tuple:

    # Set seed
    rng = np.random.default_rng(1 + seed * 10000)  # Ensure the seed is non-zero and spans a large range of values.

    # Create length-n vector u with element equal to (-1)^i/sqrt(n)
    u = np.array([(-1)**i/np.sqrt(nrow) for i in range(nrow)])
    v = np.array([(-1)**(i+1)/np.sqrt(ncol) for i in range(ncol)])

    # Generate signal
    signal = 3 * np.outer(u,v)

    # noise matrix of normal(0,1)
    noise = rng.normal(0,1,(nrow,ncol))/np.sqrt(nrow*ncol)

    # observations matrix
    X = signal + noise

    return X, u, v, signal  # return data


def experiment(*, nrow: int, ncol: int, seed: int) -> DataFrame:
    start_time = time.time()

    X, u_true, v_true, signal_true = generate_data(nrow, ncol, seed=seed)

    # Analyze the data using SVD
    U, S, Vh = np.linalg.svd(X)

    # Using first singular vector of U and V to estimate signal
    u_est = U[:,0]
    v_est = Vh[0,:]

    # Calculate estimate of signal
    signal_est = S[0] * np.outer(u_est,v_est)

    # Calculate alignment between u_est and u_true
    u_align = np.inner(u_est,u_true)

    # Calculate alignment between v_est and v_true
    v_align = np.inner(v_est,v_true)

    # Calculate distance between signal_est and signal_true
    signal_error = np.linalg.norm(signal_est-signal_true)/np.sqrt(nrow*ncol)

    # Save u_est, v_est, u_true, v_true in a CSV file with an index column
    d = {'nrow': nrow, 'ncol': ncol, 'seed': seed, "v_alignment": v_align}
    d.update({f've{i:0>3}': ve for i, ve in enumerate(v_est)})
    df = pd.DataFrame(data=d, index=[0])

    # Print runtime
    logging.info(f"Seed: {seed}; {time.time() - start_time} seconds.")
    return df


def build_params(size: int = 1, su_id: str = 'su_ID') -> dict:

    match size:
        case 1:
            exp = dict(table_name=f'stats285_{su_id}_hw5_{size}_blocks',
                        params=[{
                            'nrow': [1000],
                            'ncol': [1000],
                            'seed': [285]
                        }])
        case _:
            exp = dict(table_name=f'stats285_{su_id}_hw5_{size}_blocks',
                        params=[{
                            'nrow': [1000],
                            'ncol': [1000],
                            'seed': list(range(size))
                        }])
    return exp


def do_cluster_experiment(size: int = 1, su_id: str = 'su_ID', credentials=None):
    exp = build_params(size=size, su_id=su_id)
    with SLURMCluster(cores=8, memory='4GiB', processes=1, walltime='00:15:00') as cluster:
        cluster.scale(8)
        logging.info(cluster.job_script())
        with Client(cluster) as client:
            do_on_cluster(exp, experiment, client, credentials=credentials)
        cluster.scale(0)


def do_local_experiment(size: int = 1, su_id: str = 'su_ID', credentials=None):
    exp = build_params(size=size, su_id=su_id)
    with LocalCluster() as cluster:
        with Client(cluster) as client:
            do_on_cluster(exp, experiment, client, credentials=credentials)


if __name__ == "__main__":
    # experiment(nrow=1000, ncol=1000, seed=285)
    # do_local_experiment(size=1, su_id='su_ID_1')
    # do_local_experiment(size=1000, su_id='su_ID_slurm_large_node')
    # do_local_experiment(size=1000, su_id='su_ID_slurm_large_node_gbq',
    #                     credentials=get_gbq_credentials('stanford-stats-285-donoho-0dc233389eb9.json'))
    do_cluster_experiment(size=1000, su_id='su_ID_slurm_cluster',
                          credentials=get_gbq_credentials('stanford-stats-285-donoho-0dc233389eb9.json'))
