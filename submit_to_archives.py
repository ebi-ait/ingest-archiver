import argparse
import json
import logging
import os
import requests

from http import HTTPStatus
from colorlog import ColoredFormatter

import config


ENVIRONMENT = os.environ.get('ENVIRONMENT', 'dev')
PATH_TO_DIRECT_ARCHIVING = 'archiveSubmissions'
BIOSTUDIES_STUDY_URL = config.BIOSTUDIES_STUDY_URL
BIOSAMPLES_SAMPLE_URL = config.BIOSAMPLES_URL
ENA_WEBIN_BASE_URL = config.ENA_WEBIN_BROWSER_BASE_URL


def setup_logger():
    log = logging.getLogger(__name__)
    log.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = ColoredFormatter('%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s%(reset)s')
    ch.setFormatter(formatter)
    log.addHandler(ch)

    return log


def get_index_page():
    if ENVIRONMENT != 'prod':
        root_page = f'https://archiver.ingest.{ENVIRONMENT}.archive.data.humancellatlas.org/'
    else:
        root_page = f'https://archiver.ingest.archive.data.humancellatlas.org/'

    return root_page


def check_archiver_service_availability():
    try:
        index_page = requests.head(archiver_root)
    except requests.exceptions.RequestException:
        return False

    return index_page.status_code == HTTPStatus.OK


def create_archiving_payload() -> dict:
    return {
        'submission_uuid': submission_uuid,
        'is_direct_archiving': True
    }


def get_header():
    api_key = os.environ.get('ARCHIVER_API_KEY', None)

    return {
        'Api-Key': api_key
    }


def process_archiver_response():
    response_text = archiver_response.json()
    submitted_samples_in_biosamples =\
        [f'{BIOSAMPLES_SAMPLE_URL}/{sample_accession}' for sample_accession in response_text.get('biosamples_accessions')]
    submitted_project_in_biostudies =\
        [f'{BIOSTUDIES_STUDY_URL}{biostudies_accession}' for biostudies_accession in response_text.get('biostudies_accessions')]
    submitted_entities_in_ena =\
        [f'{ENA_WEBIN_BASE_URL}{ena_accession}' for ena_accession in response_text.get('ena_accessions')]
    return {
        'Submitted samples in BioSamples': submitted_samples_in_biosamples,
        'Submitted studies in BioStudies': submitted_project_in_biostudies,
        'Submitted entities in ENA': submitted_entities_in_ena
    }


if __name__ == "__main__":
    logger = setup_logger()

    parser = argparse.ArgumentParser(description='Submits data to archives')
    parser.add_argument('submission_uuid', type=str, help='Ingest submission UUID')

    args = parser.parse_args()

    archiver_root = get_index_page()

    if not check_archiver_service_availability():
        raise SystemExit('Archiver is not running. Please, execute it to be able to use this application.')

    logger.info(
        f"Archiving has started in {ENVIRONMENT} environment. This could take some minutes. Please, be patience.")

    submission_uuid = args.submission_uuid
    payload = create_archiving_payload()

    header = get_header()

    archiver_response = requests.post(archiver_root + PATH_TO_DIRECT_ARCHIVING,
                                      json=payload,
                                      headers=header)

    logger.info(f'Response: {archiver_response.json()}')

    archiver_response_with_urls = process_archiver_response()

    logger.info("You can check the result of archiving in the following webpages:")
    logger.info(json.dumps(archiver_response_with_urls, indent=4))
