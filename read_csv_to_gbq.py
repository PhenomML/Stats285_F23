#!/usr/bin/env python3

import logging
import os
import pandas as pd
from google.oauth2 import service_account
from EMS.manager import get_gbq_credentials

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def read_csv_to_gbq(path: str, table_name: str, credentials: service_account.credentials = None):
    exp_path = os.path.expanduser(path)
    df = pd.read_csv(exp_path)
    logger.info(f'{df}')
    df.to_gbq(table_name,
              if_exists='replace',
              progress_bar=False,
              credentials=credentials)


if __name__ == "__main__":
    credentials = get_gbq_credentials('stanford-stats-285-donoho-0dc233389eb9.json')
    read_csv_to_gbq('~/Downloads/higgs-boson/test.csv', 'XYZ.higgs_boson_test', credentials=credentials)
