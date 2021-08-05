import argparse
import logging
from api.ingest import IngestAPI


TOKEN = '<TOKEN>'

INGEST_URL = 'https://api.ingest.dev.archive.data.humancellatlas.org/'


def get_submission():
    submission_url = \
        f'{INGEST_URL}/submissionEnvelopes/search/findByUuidUuid?uuid={submission_uuid}'

    return ingest_api.get_entity(submission_url)


def remove_run_accessions(files):
    logger.info('Accessing removing started')
    for file in files:
        file_id = ingest_api.get_entity_id(file, 'files')
        file_content = file['content']
        file_content.pop('insdc_run_accessions', None)
        patch = {
            'content': file_content
        }
        ingest_api.patch_entity_by_id('files', file_id, patch)
        logger.debug(f'File with id: {file_id} has been processed')
    logger.info('Accessing removing ended')


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser(
        description='Clear run accessions from the file metadata in Ingest'
    )
    parser.add_argument('--ingest_submission_uuid', type=str, help='Ingest submission UUID')

    args = parser.parse_args()
    submission_uuid = args.ingest_submission_uuid

    ingest_api = IngestAPI(INGEST_URL)
    ingest_api.set_token(TOKEN)

    submission = get_submission()

    files_by_submission_id = list(ingest_api.get_related_entity(submission, 'files', 'files'))

    remove_run_accessions(files_by_submission_id)
