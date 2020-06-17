"""App entry point."""
import json
import logging
import sys
import threading
import time
from http import HTTPStatus

from flask import Flask
from flask import jsonify
from flask import request

import config
from api.dsp import DataSubmissionPortal
from api.ingest import IngestAPI
from archiver.archiver import IngestArchiver, ArchiveSubmission, ArchiveEntityMap


def create_app():
    """Construct the core application."""
    app = Flask(__name__)
    return app


app = create_app()


@app.route("/")
def index():
    return "Ingest Archiver is running"


@app.route("/archiveSubmissions", methods=['POST'])
def archive():
    data = request.get_json()

    submission_uuid = data.get('submission_uuid')
    exclude_types = data.get('exclude_types')
    alias_prefix = data.get('alias_prefix')

    if not submission_uuid:
        error = {
            'message': f'You must supply the parameter submission_uuid referring to an Ingest submission envelope uuid.'
        }
        return response_json(HTTPStatus.BAD_REQUEST, error)

    ingest_api = IngestAPI(config.INGEST_API_URL)
    archiver = IngestArchiver(ingest_api=ingest_api,
                              dsp_api=DataSubmissionPortal(config.DSP_API_URL),
                              exclude_types=exclude_types,
                              alias_prefix=alias_prefix)

    thread = threading.Thread(target=async_archive,
                              args=(ingest_api, archiver, submission_uuid))
    thread.start()

    response = {
        'message': 'successfully triggered!'
    }

    return jsonify(response)


def async_archive(ingest_api: IngestAPI, archiver: IngestArchiver, submission_uuid: str):
    print('Starting...')
    start = time.time()
    manifests = ingest_api.get_manifest_ids_from_submission(submission_uuid)
    entity_map: ArchiveEntityMap = archiver.convert(manifests)
    dsp_submission, ingest_tracker = archiver.archive_metadata(entity_map)
    archiver.notify_file_archiver(dsp_submission)
    ingest_tracker.patch_archive_submission({
        'submissionUuid': submission_uuid,
        'fileUploadPlan': dsp_submission.file_upload_info
    })
    end = time.time()
    print(f'Creating DSP submission for {submission_uuid} finished in {end - start}s')


@app.route('/archiveSubmissions/<dsp_submission_uuid>')
def get_submission(dsp_submission_uuid: str):
    ingest_api = IngestAPI(config.INGEST_API_URL)
    ingest_archive_submission = ingest_api.get_archive_submission_by_dsp_uuid(dsp_submission_uuid)
    del ingest_archive_submission['_links']
    return jsonify(ingest_archive_submission)


@app.route('/archiveSubmissions/<dsp_submission_uuid>/entities')
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
def get_validation_errors(archive_submission_uuid: str):
    dsp_api = DataSubmissionPortal(config.DSP_API_URL)
    submission_url = dsp_api.get_submission_url(archive_submission_uuid)
    submission = ArchiveSubmission(dsp_api=dsp_api, dsp_submission_url=submission_url)
    validation_errors = submission.get_validation_error_report()
    return jsonify(validation_errors)


@app.route('/archiveSubmissions/<archive_submission_uuid>/validationResult')
def get_validation_result(archive_submission_uuid: str):
    dsp_api = DataSubmissionPortal(config.DSP_API_URL)
    submission_url = dsp_api.get_submission_url(archive_submission_uuid)
    submission = ArchiveSubmission(dsp_api=dsp_api, dsp_submission_url=submission_url)
    result = submission.get_all_validation_result_details()
    return jsonify(result)


@app.route('/archiveSubmissions/<archive_submission_uuid>/blockers')
def get_blockers(archive_submission_uuid: str):
    dsp_api = DataSubmissionPortal(config.DSP_API_URL)
    submission_url = dsp_api.get_submission_url(archive_submission_uuid)
    submission = ArchiveSubmission(dsp_api=dsp_api, dsp_submission_url=submission_url)
    blockers = submission.get_blockers()
    return jsonify(blockers)


@app.route('/archiveSubmissions/<archive_submission_uuid>/submit', methods=['POST'])
def submit(archive_submission_uuid: str):
    dsp_api = DataSubmissionPortal(config.DSP_API_URL)
    submission_url = dsp_api.get_submission_url(archive_submission_uuid)
    submission = ArchiveSubmission(dsp_api=dsp_api, dsp_submission_url=submission_url)
    if submission.is_submittable():
        submission.submit()
        data = {
            'message': f'DSP Submission {submission.dsp_uuid} was submitted successfully'
        }
        return response_json(HTTPStatus.ACCEPTED, data=data)

    data = {
        'message': f'DSP submission {archive_submission_uuid} is not submittable.'
        f' Please make sure that the validation is passing and there are no submission blockers'
    }
    return response_json(HTTPStatus.BAD_REQUEST, data=data)


@app.route('/archiveSubmissions/<dsp_submission_uuid>/complete', methods=['POST'])
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
    print('Starting...')
    start = time.time()
    ingest_archive_submission = ingest_api.get_archive_submission_by_dsp_uuid(dsp_submission_uuid)
    ingest_entities = ingest_api.get_related_entity(ingest_archive_submission, 'entities', 'archiveEntities')
    entity_map = ArchiveEntityMap.map_from_ingest_entities(ingest_entities)
    dsp_submission_url = dsp_api.get_submission_url(dsp_submission_uuid)
    archiver = IngestArchiver(ingest_api=ingest_api,
                              dsp_api=dsp_api)
    archive_submission = archiver.complete_submission(dsp_submission_url, entity_map)
    end = time.time()
    print(f'Completed DSP submission for {dsp_submission_uuid} in {end - start}s')
    return archive_submission


def response_json(status_code, data):
    response = app.response_class(
        response=json.dumps(data),
        status=status_code,
        mimetype='application/json'
    )
    return response


logging.getLogger('archiver').setLevel(logging.INFO)
logging.getLogger('archiver.archiver.IngestArchiver').setLevel(logging.INFO)

format = ' %(asctime)s  - %(name)s - %(levelname)s in %(filename)s:' \
         '%(lineno)s %(funcName)s(): %(message)s'
logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                    format=format)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    app.run(host='0.0.0.0')
