#!/usr/bin/env python3

import argparse
import pandas as pd
from EMS.manager import get_gbq_credentials
import sys
import logging

logging.basicConfig(level=logging.INFO)


def parse() -> tuple:
    logging.info(f'{" ".join(sys.argv)}')
    parser = argparse.ArgumentParser(prog='concat_csv_to_gbq')
    parser.add_argument('table_name', type=str)
    parser.add_argument('files', type=str, nargs='*')
    args = parser.parse_args()
    return args.table_name, args.files


def concat_csv_to_df(files: list) -> pd.DataFrame:
    dfs = []
    for f in files:
        dfs.append(pd.read_csv(f))
    df = pd.concat(dfs)
    df.reset_index(drop=True, inplace=True)
    return df


def df_to_gbq(df: pd.DataFrame, table_name: str):
    cred = get_gbq_credentials('stanford-stats-285-donoho-0dc233389eb9.json')
    df.to_gbq(f'HW5.{table_name}',
              if_exists='append',
              progress_bar=False,
              credentials=cred)


def concat_csv_to_gbq() -> pd.DataFrame:
    table_name, files = parse()
    df = concat_csv_to_df(files)
    df_to_gbq(df, table_name)
    return df


if __name__ == "__main__":
    _ = concat_csv_to_gbq()
    # df.to_csv(sys.stdout, index=False)
