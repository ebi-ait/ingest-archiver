"""App entry point."""
import logging
import sys
import threading

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
    project_uuid = data.get('project_uuid')
    exclude_types = data.get('exclude_types')
    alias_prefix = data.get('alias_prefix')
    ingest_api = IngestAPI(config.INGEST_API_URL)
    archiver = IngestArchiver(ingest_api=ingest_api,
                              dsp_api=DataSubmissionPortal(config.DSP_API_URL),
                              exclude_types=exclude_types,
                              alias_prefix=alias_prefix)

    thread = threading.Thread(target=async_archive,
                              args=(ingest_api, archiver, project_uuid))
    thread.start()

    response = {
        'message': 'successfully triggered!'
    }

    return jsonify(response)


@app.route('/archiveSubmissions/<archive_submission_uuid>/validationErrors')
def validation_report(archive_submission_uuid: str):
    dsp_api = DataSubmissionPortal(config.DSP_API_URL)
    submission_url = dsp_api.get_submission_url(archive_submission_uuid)
    submission = ArchiveSubmission(dsp_api=dsp_api, dsp_submission_url=submission_url)
    validation_errors = submission.get_validation_error_report()
    return jsonify(validation_errors)


def async_archive(ingest_api: IngestAPI, archiver: IngestArchiver, project_uuid: str):
    print('starting')
    manifests = ingest_api.get_manifest_ids(project_uuid=project_uuid)
    print(manifests)
    entity_map: ArchiveEntityMap = archiver.convert(manifests)
    dsp_submission = archiver.archive_metadata(entity_map)
    messages = archiver.notify_file_archiver(dsp_submission)
    print('finished')

logging.getLogger('archiver').setLevel(logging.INFO)
logging.getLogger('archiver.archiver.IngestArchiver').setLevel(logging.INFO)

format = ' %(asctime)s  - %(name)s - %(levelname)s in %(filename)s:' \
         '%(lineno)s %(funcName)s(): %(message)s'
logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                    format=format)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    app.run(host='0.0.0.0')