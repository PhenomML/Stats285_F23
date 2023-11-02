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

    d = {'nrow': nrow, 'ncol': ncol, 'seed': seed, "v_alignment": v_align}
    d.update({f've{i:0>3}': ve for i, ve in enumerate(v_est)})
    df = pd.DataFrame(data=d, index=[0])

    # Print runtime
    logging.info(f"Seed: {seed}; {time.time() - start_time} seconds.")
    return df


def parse() -> tuple:
    parser = argparse.ArgumentParser(prog='map_function')
    parser.add_argument('nrow', type=int)
    parser.add_argument('ncol', type=int)
    parser.add_argument('task_id', type=int)
    parser.add_argument('table_name', type=str)
    args = parser.parse_args()
    return args.nrow, args.ncol, args.task_id, args.table_name


def parse_reduction() -> tuple:
    parser = argparse.ArgumentParser(prog='reduce_function')
    # parser.add_argument('nrow', type=int)
    # parser.add_argument('ncol', type=int)
    # parser.add_argument('seed', type=int)
    parser.add_argument('table_name', type=str)
    args = parser.parse_args()
    return args.table_name


def do_sbatch_array():
    nrow, ncol, task_id, table_name = parse()
    cred = get_gbq_credentials('stanford-stats-285-donoho-0dc233389eb9.json')

    results =[]
    for s in range(task_id, task_id + 100):
        results.append(experiment(nrow=nrow, ncol=ncol, seed=s))
    df = pd.concat(results)
    if task_id > 0:  # Delay every write except the first.
        time.sleep(np.random.randint(10, 15))
    df.to_gbq(f'HW4.{table_name}',
              if_exists='append',
              progress_bar=False,
              credentials=cred)


if __name__ == "__main__":
    # experiment(nrow=1000, ncol=1000, seed=285)
    do_sbatch_array()
