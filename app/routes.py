from flask import current_app as app, jsonify
from flask import request

import config
from api.dsp import DataSubmissionPortal
from api.ingest import IngestAPI
from app.models import ArchiveEntity, ArchiveSubmission
from archiver.archiver import IngestArchiver, ArchiveEntityMap


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

    manifests = ingest_api.get_manifest_ids(project_uuid=project_uuid)
    archiver = IngestArchiver(ingest_api=ingest_api,
                              dsp_api=DataSubmissionPortal(config.DSP_API_URL),
                              exclude_types=exclude_types,
                              alias_prefix=alias_prefix)

    if project_uuid:
        archive_submission = ArchiveSubmission()
        archive_submission.save()
        entity_map: ArchiveEntityMap = archiver.convert(manifests)

        for entity in entity_map.get_entities():
            archive_entity = ArchiveEntity(submission_id=archive_submission.id,
                                           content=entity.conversion,
                                           type=entity.archive_entity_type)
            archive_entity.save()

    return jsonify(entity_map.get_conversion_summary())


@app.route('/archiveEntities')
def archive_entities():
    submission_id = request.args.get('submission_id')
    page = request.args.get('page', 1)
    per_page = 20
    if submission_id:
        query = ArchiveEntity.query.filter_by(submission_id=submission_id)
    else:
        query = ArchiveEntity.query

    paged_entities = query.paginate(int(page), per_page, False)
    return jsonify({'archive_entities': paged_entities.items,
                    'next': paged_entities.next_num,
                    'previous': paged_entities.prev_num})
