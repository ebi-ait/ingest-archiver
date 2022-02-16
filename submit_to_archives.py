import argparse
import json
import logging
import os
import requests

from http import HTTPStatus
from colorlog import ColoredFormatter

ENVIRONMENT = os.environ.get('ENVIRONMENT', 'dev')
PATH_TO_DIRECT_ARCHIVING = 'archiveSubmissions'


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


def process_archiver_response():
    output = {}
    for archive_name, archived_items in response_json.items():
        output[archive_name] = populate_response_by_archive_name(archive_name, archived_items)

    return output


def populate_response_by_archive_name(archive_name, archived_items):
    archive_result = {}
    for status, results in archived_items.items():
        data = []
        get_response_data_from_archive(archive_name, data, results, status)
        archive_result[f'{status} entities in {archive_name}'] = data

    return archive_result


def get_response_data_from_archive(archive_name, data, results, status):
    for result_data in results:
        base_url = ARCHIVE_URLS[archive_name]
        if archive_name == 'ena':
            entity_type = result_data.get('entity_type')
            if entity_type:
                url_entities_part = ENA_URL_PART_BY_ENTITY_TYPE[entity_type]
                base_url = base_url.format(entities=url_entities_part)
        archive_response = result_data.get('data', {})
        if status != 'ERRORED':
            data.append(
                {
                    'uuid': f'{archive_response.get("uuid")}',
                    'url': f'{base_url}/{archive_response.get("accession")}'
                }
            )
        else:
            data.append(
                {
                    'uuid': f'{archive_response.get("uuid")}',
                    'error_details': result_data.get('error_messages')
                }
            )


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

    archiver_response = requests.post(archiver_root + PATH_TO_DIRECT_ARCHIVING,
                                      json=payload,
                                      headers=header)

    response_json = archiver_response.json()

    logger.info(f'Response: {response_json}')

    if response_json.get('message', None) is not None:
        logger.error("Something went wrong while sending data/metadata to archives.")
        exit(1)

    archiver_response_with_urls = process_archiver_response()

    logger.info("You can check the result of archiving in the following webpages:")
    logger.info(json.dumps(archiver_response_with_urls, indent=4))
