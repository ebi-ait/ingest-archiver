import argparse
import logging
from api.ingest import IngestAPI


logging.getLogger('ena.ena_api').setLevel(logging.DEBUG)

TOKEN = '<TOKEN>'

INGEST_URL = 'https://api.ingest.dev.archive.data.humancellatlas.org/'


def set_token_for_api():
    headers = ingest_api.get_headers()
    headers['Authorization'] = f'{TOKEN}'


def get_submission():
    submission_url = \
        f'{INGEST_URL}/submissionEnvelopes/search/findByUuidUuid?uuid={submission_uuid}'

    return ingest_api.get_entity(submission_url)


def remove_run_accessions(files):
    for file in files:
        file_id = ingest_api.get_entity_id(file, 'files')
        file_content = file['content']
        file_content.pop('insdc_run_accessions', None)
        patch = {
            'content': file_content
        }
        ingest_api.patch_entity_by_id('files', file_id, patch)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Clear run accessions from the file metadata in Ingest'
    )
    parser.add_argument('--ingest_submission_uuid', type=str, help='Ingest submission UUID')

    args = parser.parse_args()
    submission_uuid = args.ingest_submission_uuid

    ingest_api = IngestAPI(INGEST_URL)
    set_token_for_api()

    submission = get_submission()

    files_by_submission_id = list(ingest_api.get_related_entity(submission, 'files', 'files'))

    remove_run_accessions(files_by_submission_id)
