#!/usr/bin/env python3

import argparse
import pandas as pd
import sys
import logging

logging.basicConfig(level=logging.INFO)


def parse() -> list:
    logging.info(f'{" ".join(sys.argv)}')
    parser = argparse.ArgumentParser(prog='concat_df')
    parser.add_argument('files', type=str, nargs='*')
    args = parser.parse_args()
    return args.files


def concat_df():
    files = parse()
    dfs = []
    for f in files:
        dfs.append(pd.read_csv(f))
    df = pd.concat(dfs)
    df.reset_index(drop=True, inplace=True)
    # df.drop(columns=['index'], inplace=True)
    logging.info(f'{df}')
    df.to_csv(sys.stdout)


if __name__ == "__main__":
    concat_df()
