#!/usr/bin/env python3

import logging
from ucimlrepo import fetch_ucirepo, list_available_datasets
from google.oauth2 import service_account
from EMS.manager import get_gbq_credentials

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def copy_dataset_to_XYZ(dataset_id: int, table_name: str, credentials: service_account.credentials = None):
    repo = fetch_ucirepo(id=dataset_id)
    logger.info(f'{repo}')
    repo.data.original.to_gbq(table_name,
                              if_exists='replace',
                              progress_bar=False,
                              credentials=credentials)


if __name__ == "__main__":
    list_available_datasets()
    credentials = get_gbq_credentials('stanford-stats-285-donoho-0dc233389eb9.json')
    copy_dataset_to_XYZ(2, 'XYZ.adult_income', credentials=credentials)
    copy_dataset_to_XYZ(31, 'XYZ.forest_covertype', credentials=credentials)
