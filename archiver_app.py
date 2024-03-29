"""App entry point."""
import json
import logging
import sys
import threading
import time
from http import HTTPStatus
from functools import wraps

from biostudiesclient.exceptions import RestErrorException
from flask import Flask, Response
from flask import jsonify
from flask import request
from requests import HTTPError

import config
from api.dsp import DataSubmissionPortal
from api.ingest import IngestAPI
from archiver import ArchiveException
from archiver.archiver import IngestArchiver, ArchiveSubmission, ArchiveEntityMap
from archiver.data_archiver import DataArchiver, DataArchiverMessageBroker
from archiver.direct import direct_archiver_from_config


format = ' %(asctime)s  - %(name)s - %(levelname)s in %(filename)s:' \
         '%(lineno)s %(funcName)s(): %(message)s'
logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                    format=format)

logging.getLogger('archiver').setLevel(logging.INFO)
logging.getLogger('api').setLevel(logging.INFO)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def create_app():
    """Construct the core application."""
    app = Flask(__name__)
    return app


app = create_app()


def require_apikey(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        apikey = request.headers.get('Api-Key')

        if apikey is None:
            return response_json(HTTPStatus.UNAUTHORIZED, {'message': 'header missing Api-Key'})

        if apikey == config.ARCHIVER_API_KEY:
            return func(*args, **kwargs)
        else:
            return response_json(HTTPStatus.UNAUTHORIZED, {'message': 'invalid Api-Key'})

    return decorator


@app.route("/")
def index():
    return "Ingest Archiver is running"


@app.route("/archiveSubmissions", methods=['POST'])
@require_apikey
def archive():
    data = request.get_json()

    submission_uuid = data.get('submission_uuid')
    exclude_types = data.get('exclude_types')
    alias_prefix = data.get('alias_prefix')
    is_direct_archiving = data.get('is_direct_archiving')

    logger.info('Archiving started with UUID=%s', submission_uuid)

    if not is_direct_archiving:
        is_direct_archiving = config.DIRECT_SUBMISSION

    if not submission_uuid:
        error = {
            'message': f'You must supply the parameter submission_uuid referring to an Ingest submission envelope uuid.'
        }
        return response_json(HTTPStatus.BAD_REQUEST, error)

    if is_direct_archiving:
        archives_response = {}
        ingest_api = IngestAPI(config.INGEST_API_URL)
        try:
            archive_job = create_archive_job(ingest_api, submission_uuid)
            direct_archiver = direct_archiver_from_config()

            thread = threading.Thread(target=direct_archiver.archive_submission,
                                      args=(submission_uuid, archive_job, ingest_api))
            thread.start()

            archives_response = {
                'message': 'Direct archiving successfully triggered!',
                'archiveJob': archive_job
            }
            logger.info('Direct archiving started with UUID=%s', submission_uuid)
        except ArchiveException as rest_error:
            set_archive_job_to_fail(ingest_api, archive_job, archives_response)
            archives_response.update(
                __handle_error_archive_response(
                    rest_error.message, rest_error.status_code, submission_uuid, rest_error.archive_name))
        except RestErrorException as rest_error:
            set_archive_job_to_fail(ingest_api, archive_job, archives_response)
            archives_response.update(
                __handle_error_archive_response(
                    rest_error.message, rest_error.status_code, submission_uuid))
        except HTTPError as rest_error:
            set_archive_job_to_fail(ingest_api, archive_job, archives_response)
            archives_response.update(
                __handle_error_archive_response(
                    rest_error.response.text, rest_error.response.status_code, submission_uuid))
    else:
        ingest_api = IngestAPI(config.INGEST_API_URL)
        archiver = IngestArchiver(ingest_api=ingest_api,
                                  dsp_api=DataSubmissionPortal(config.DSP_API_URL),
                                  exclude_types=exclude_types,
                                  alias_prefix=alias_prefix)

        thread = threading.Thread(target=async_archive,
                                  args=(ingest_api, archiver, submission_uuid))
        thread.start()

        archives_response = {
            'message': 'successfully triggered!'
        }

    return jsonify(archives_response)


def create_archive_job(ingest_api: IngestAPI, submission_uuid: str):
    payload = {
        "submissionUuid": submission_uuid
    }
    response = ingest_api.create_archive_job(payload=payload)

    return response


def set_archive_job_to_fail(ingest_api: IngestAPI, archive_job: dict, archives_response: dict):
    payload = {
        "overallStatus": "Failed"
    }
    entity_id = archive_job.get("_links", {}).get("self", {}).get("href", "").rsplit("/")[-1]
    response = ingest_api.patch_entity_by_id(
        entity_type="archiveJobs",
        entity_id=entity_id,
        entity_patch=payload
    )

    archives_response.update({'archiveJob': response})

    return response


@app.route("/archiveSubmissions/data", methods=['POST'])
@require_apikey
def archive_data():
    message_broker = DataArchiverMessageBroker()
    response = DataArchiver(message_broker).send_request(request.get_json())
    return jsonify(response)

@app.route("/archiveSubmissions/data/<submission_uuid>")
@require_apikey
def archive_data_result(submission_uuid):
    ingest_api = IngestAPI(config.INGEST_API_URL)
    submission = ingest_api.get_submission_by_uuid(submission_uuid)
    files = list(ingest_api.get_related_entity(submission, 'files', 'files'))
    sequence_files = list(filter(lambda f: f['content']['describedBy'].endswith('sequence_file'), files))
    file_archive_results = list(map(file_archive_result, sequence_files))
    response = {
        'message': 'Data archiving result',
        'sub_uuid': submission_uuid,
        'files': file_archive_results
    }
    return jsonify(response)


def file_archive_result(file):
    return {
                'uuid': file['uuid']['uuid'],
                'file_name': file['content']['file_core']['file_name'],
                'cloud_url': file['cloudUrl'],
                'fileArchiveResult': file['fileArchiveResult']
            }


def __handle_error_archive_response(error_message, status_code, submission_uuid, archive_name: str = None):
    log_error_message(error_message, status_code, submission_uuid)
    response = {
        'message': 'Archiving failed.',
        'detailed_error_message': error_message,
        'error_status_code': status_code
    }

    if archive_name:
        response.update({'archive': archive_name})

    return response


def log_error_message(error_message, status_code, submission_uuid):
    logger.error('Archiving submission with UUID=%s failed.', submission_uuid)
    logger.error('Archive responded with status code: %s', status_code)
    logger.error('Archive responded with this error message: %s', error_message)


def async_archive(ingest_api: IngestAPI, archiver: IngestArchiver, submission_uuid: str):
    logger.info('Starting...')
    start = time.time()
    manifests = ingest_api.get_manifest_ids_from_submission(submission_uuid)

    try:
        entity_map: ArchiveEntityMap = archiver.convert(manifests)
        dsp_submission, ingest_tracker = archiver.archive_metadata(entity_map)
        archiver.notify_file_archiver(dsp_submission)
        ingest_tracker.patch_archive_submission({
            'submissionUuid': submission_uuid,
            'fileUploadPlan': dsp_submission.file_upload_info
        })
        end = time.time()
        logger.info(f'Creating DSP submission for {submission_uuid} finished in {end - start}s')
    except Exception as e:
        logger.exception(e)
        raise


@app.route('/latestArchiveSubmission/<ingest_submission_uuid>')
@require_apikey
def get_latest_archive_submission(ingest_submission_uuid):
    ingest_api = IngestAPI(config.INGEST_API_URL)
    latest_archive_submission = ingest_api.get_latest_archive_submission_by_submission_uuid(ingest_submission_uuid)

    if not latest_archive_submission:
        return response_json(HTTPStatus.NOT_FOUND, None)

    del latest_archive_submission['_links']
    return jsonify(latest_archive_submission)


@app.route('/archiveSubmissions/<dsp_submission_uuid>')
@require_apikey
def get_submission(dsp_submission_uuid: str):
    ingest_api = IngestAPI(config.INGEST_API_URL)
    ingest_archive_submission = ingest_api.get_archive_submission_by_dsp_uuid(dsp_submission_uuid)
    del ingest_archive_submission['_links']
    return jsonify(ingest_archive_submission)


@app.route('/archiveSubmissions/<dsp_submission_uuid>', methods=['DELETE'])
@require_apikey
def delete_archive_submission(dsp_submission_uuid: str):
    ingest_api = IngestAPI(config.INGEST_API_URL)
    dsp_api = DataSubmissionPortal(config.DSP_API_URL)
    ingest_archive_submission = ingest_api.get_archive_submission_by_dsp_uuid(dsp_submission_uuid)
    dsp_url = ingest_archive_submission['dspUrl']
    dsp_api.delete_submission(dsp_url)
    logger.info(f'Deleting DSP submission {dsp_url}')
    archive_submission_url = ingest_archive_submission['_links']['self']['href']
    logger.info(f'Deleting Ingest Archive Submission {archive_submission_url}')
    response = ingest_api.delete(archive_submission_url)
    return response_json(HTTPStatus.OK, data=response)


@app.route('/archiveSubmissions/<dsp_submission_uuid>/fileUploadPlan', methods=['GET'])
@require_apikey
def sendFile(dsp_submission_uuid: str):
    ingest_api = IngestAPI(config.INGEST_API_URL)
    ingest_archive_submission = ingest_api.get_archive_submission_by_dsp_uuid(dsp_submission_uuid)
    jobs = ingest_archive_submission.get('fileUploadPlan')
    content = json.dumps({'jobs': jobs}, indent=4)

    filename = f'FILE_UPLOAD_PLAN_{dsp_submission_uuid}.json'
    return Response(content,
                    mimetype='application/json',
                    headers={'Content-Disposition': f'attachment;filename={filename}'})


@app.route('/archiveSubmissions/<dsp_submission_uuid>/entities')
@require_apikey
def get_submission_entities(dsp_submission_uuid: str):
    ingest_api = IngestAPI(config.INGEST_API_URL)
    ingest_archive_submission = ingest_api.get_archive_submission_by_dsp_uuid(dsp_submission_uuid)
    entities_url = ingest_archive_submission['_links']['entities']['href']
    params = request.args
    response_body = ingest_api.get(entities_url, params=params)
    result = {
        'entities': response_body['_embedded']['archiveEntities'],
        'page': response_body.get('page')
    }

    for entity in result['entities']:
        del entity['_links']

    return jsonify(result)


@app.route('/archiveSubmissions/<archive_submission_uuid>/validationErrors')
@require_apikey
def get_validation_errors(archive_submission_uuid: str):
    dsp_api = DataSubmissionPortal(config.DSP_API_URL)
    submission_url = dsp_api.get_submission_url(archive_submission_uuid)
    submission = ArchiveSubmission(dsp_api=dsp_api, dsp_submission_url=submission_url)
    validation_errors = submission.get_validation_error_report()
    return jsonify(validation_errors)


@app.route('/archiveSubmissions/<archive_submission_uuid>/validationResult')
@require_apikey
def get_validation_result(archive_submission_uuid: str):
    dsp_api = DataSubmissionPortal(config.DSP_API_URL)
    submission_url = dsp_api.get_submission_url(archive_submission_uuid)
    submission = ArchiveSubmission(dsp_api=dsp_api, dsp_submission_url=submission_url)
    result = submission.get_all_validation_result_details()
    return jsonify(result)


@app.route('/archiveSubmissions/<archive_submission_uuid>/blockers')
@require_apikey
def get_blockers(archive_submission_uuid: str):
    dsp_api = DataSubmissionPortal(config.DSP_API_URL)
    submission_url = dsp_api.get_submission_url(archive_submission_uuid)
    submission = ArchiveSubmission(dsp_api=dsp_api, dsp_submission_url=submission_url)
    blockers = submission.get_blockers()
    return jsonify(blockers)


@app.route('/archiveSubmissions/<dsp_submission_uuid>/complete', methods=['POST'])
@require_apikey
def complete(dsp_submission_uuid: str):
    dsp_api = DataSubmissionPortal(config.DSP_API_URL)
    ingest_api = IngestAPI(config.INGEST_API_URL)

    thread = threading.Thread(target=async_complete,
                              args=(dsp_api, dsp_submission_uuid, ingest_api))
    thread.start()

    response = {
        'message': 'successfully triggered!'
    }
    return response_json(HTTPStatus.ACCEPTED, data=response)


def async_complete(dsp_api, dsp_submission_uuid, ingest_api):
    logger.info('Starting...')
    start = time.time()
    ingest_archive_submission = ingest_api.get_archive_submission_by_dsp_uuid(dsp_submission_uuid)
    ingest_entities = ingest_api.get_related_entity(ingest_archive_submission, 'entities', 'archiveEntities')
    entity_map = ArchiveEntityMap.map_from_ingest_entities(ingest_entities)
    dsp_submission_url = dsp_api.get_submission_url(dsp_submission_uuid)
    archiver = IngestArchiver(ingest_api=ingest_api,
                              dsp_api=dsp_api)
    archive_submission = archiver.complete_submission(dsp_submission_url, entity_map)
    end = time.time()
    logger.info(f'Completed DSP submission for {dsp_submission_uuid} in {end - start}s')
    return archive_submission


def response_json(status_code, data):
    response = app.response_class(
        response=json.dumps(data),
        status=status_code,
        mimetype='application/json'
    )
    return response


if __name__ == "__main__":
    format = ' %(asctime)s  - %(name)s - %(levelname)s in %(filename)s:' \
             '%(lineno)s %(funcName)s(): %(message)s'
    logging.basicConfig(stream=sys.stdout, level=logging.WARNING,
                        format=format)
    app.run(host='0.0.0.0')
