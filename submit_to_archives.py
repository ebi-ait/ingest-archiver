import argparse
import json
import logging
import os
import requests

from http import HTTPStatus
from colorlog import ColoredFormatter

ERROR_MESSAGE_WENT_WRONG = "Something went wrong while sending data/metadata to archives."

ENVIRONMENT = os.environ.get('ENVIRONMENT', 'dev')
DIRECT_ARCHIVING_ENDPOINT = 'archiveSubmissions'


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
    if ENVIRONMENT == 'local':
        root_page = 'http://localhost:5000/'
    elif ENVIRONMENT != 'prod':
        root_page = f'https://archiver.ingest.{ENVIRONMENT}.archive.data.humancellatlas.org/'
    else:
        root_page = f'https://archiver.ingest.archive.data.humancellatlas.org/'

    return root_page


def setup_archive_urls():
    global ENA_URL_PART_BY_ENTITY_TYPE, ARCHIVE_URLS, BIOSTUDIES_STUDY_URL, BIOSAMPLES_SAMPLE_URL, ENA_WEBIN_BASE_URL
    if ENVIRONMENT == 'prod':
        BIOSTUDIES_STUDY_URL = 'https://www.ebi.ac.uk/biostudies/studies'
        BIOSAMPLES_SAMPLE_URL = 'https://www.ebi.ac.uk/biosamples/samples'
        ENA_WEBIN_BASE_URL = 'https://www.ebi.ac.uk/ena/submit/webin/report/{entities}'
    else:
        BIOSTUDIES_STUDY_URL = 'https://wwwdev.ebi.ac.uk/biostudies/studies'
        BIOSAMPLES_SAMPLE_URL = 'https://wwwdev.ebi.ac.uk/biosamples/samples'
        ENA_WEBIN_BASE_URL = 'https://wwwdev.ebi.ac.uk/ena/submit/webin/report/{entities}'

    ARCHIVE_URLS = {
        'biosamples': BIOSAMPLES_SAMPLE_URL,
        'biostudies': BIOSTUDIES_STUDY_URL,
        'ena': ENA_WEBIN_BASE_URL
    }

    ENA_URL_PART_BY_ENTITY_TYPE = {
        'biomaterials': 'samples',
        'projects': 'studies'
    }


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


if __name__ == "__main__":
    logger = setup_logger()

    parser = argparse.ArgumentParser(description='Submits data to archives')
    parser.add_argument('submission_uuid', type=str, help='Ingest submission UUID')

    args = parser.parse_args()

    archiver_root = get_index_page()

    setup_archive_urls()

    if not check_archiver_service_availability():
        raise SystemExit('Archiver is not running. Please, execute it to be able to use this application.')

    submission_uuid = args.submission_uuid
    payload = create_archiving_payload()

    header = get_header()

    logger.info(
        f"Archiving has started in {ENVIRONMENT} environment for submission: {submission_uuid}."
        f" This could take some time. Please, be patience.")

    archiver_response = requests.post(archiver_root + DIRECT_ARCHIVING_ENDPOINT,
                                      json=payload,
                                      headers=header)

    if archiver_response.status_code != HTTPStatus.OK:
        logger.info(ERROR_MESSAGE_WENT_WRONG)
        logger.info(f'HTTP Status code: {archiver_response.status_code}')
        logger.info(f'HTTP Response: {str(archiver_response.content)}')
    else:
        response_json = archiver_response.json()

        logger.info(json.dumps(response_json, indent=4))
