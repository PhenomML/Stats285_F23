#!/usr/bin/env python3

import time
import numpy as np
import pandas as pd
from pandas import DataFrame
from dask.distributed import Client, LocalCluster
from dask_jobqueue import SLURMCluster
from EMS.manager import do_on_cluster, get_gbq_credentials
import argparse
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
    # Begin saving runtime
    start_time = time.time()

    # Generate data
    # seed = 285
    # nrow = 1000
    # ncol = 1000
    X, u_true, v_true, signal_true = generate_data(nrow, ncol, seed=seed)

    logging.info('Data Generated')

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

    # Print results to text file
    logging.info(f"nrow = {nrow}")
    logging.info(f"ncol = {ncol}")
    logging.info(f"u_alignment = {u_align}")
    logging.info(f"v_alignment = {v_align}")
    logging.info(f"signal_error = {signal_error}")

    # Save u_est, v_est, u_true, v_true in a CSV file with an index column
    df = pd.DataFrame({'nrow': nrow, 'ncol': ncol, 'seed': seed,  # P, Parameters
                       "u_est": u_est, "v_est": v_est, "u_true": u_true, "v_true": v_true,  # W, Observables
                       "u_alignment": u_align, "v_alignment": v_align, "signal_error": signal_error})
    # df.to_csv("hw2data.csv", index_label="index")

    # Print runtime
    logging.info(f"--- {time.time() - start_time} seconds ---")
    return df


def build_params(size: int = 1, su_id: str = 'su_ID') -> dict:

    match size:
        case 1:
            exp = dict(table_name=f'stats285_{su_id}_hw4_{size}_blocks',
                        params=[{
                            'nrow': [1000],
                            'ncol': [1000],
                            'seed': [285]
                        }])
        case _:
            exp = dict(table_name=f'stats285_{su_id}_hw4_{size}_blocks',
                        params=[{
                            'nrow': [1000],
                            'ncol': [1000],
                            'seed': list(range(size))
                        }])
    return exp


def do_cluster_experiment():
    exp = build_params(size=1000, su_id='adonoho_2')
    with SLURMCluster(cores=8, memory='4GiB', processes=1, walltime='00:30:00') as cluster:
        cluster.scale(8)
        with Client(cluster) as client:
            # do_on_cluster(exp, experiment, client)
            do_on_cluster(exp, experiment, client, credentials=get_gbq_credentials())
        cluster.scale(0)


def do_local_experiment():
    exp = build_params(size=1000, su_id='adonoho_1')
    with LocalCluster() as cluster:
        with Client(cluster) as client:
            # do_on_cluster(exp, experiment, client)
            do_on_cluster(exp, experiment, client, credentials=get_gbq_credentials())


def parse() -> tuple:
    parser = argparse.ArgumentParser(prog='map_function')
    parser.add_argument('nrow', type=int)
    parser.add_argument('ncol', type=int)
    parser.add_argument('seed', type=int)
    parser.add_argument('table_name', type=str)
    args = parser.parse_args()
    return args.nrow, args.ncol, args.seed, args.table_name


from random import randint
from time import sleep

def do_sbatch_array():
    nrow, ncol, seed, table_name = parse()
    cred = get_gbq_credentials('stanford-stats-285-donoho-0dc233389eb9.json')

    results =[]
    for s in range(seed, seed + 100):
        results.append(experiment(nrow=nrow, ncol=ncol, seed=s))
        if not(len(results) % 50):  # Write twice.
            df = pd.concat(results)
            results = []
            sleep(randint(10, 30))
            df.to_gbq(f'HW4.{table_name}',
                      if_exists='append',
                      progress_bar=False,
                      credentials=cred)


if __name__ == "__main__":
    # experiment(nrow=1000, ncol=1000, seed=285)
    do_sbatch_array()
    # do_local_experiment()
    # do_cluster_experiment()
