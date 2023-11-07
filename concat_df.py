#!/usr/bin/env python3

import argparse
import pandas as pd
import sys


def parse() -> list:
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
    df.to_csv(sys.stdout)


if __name__ == "__main__":
    concat_df()
