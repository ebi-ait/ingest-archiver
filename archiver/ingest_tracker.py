from typing import List

from ingest.importer.submission import EntityMap

from api.ingest import IngestAPI
from archiver.submission import ArchiveEntity, ArchiveSubmission


class IngestTracker:
    def __init__(self, ingest_api: IngestAPI):
        self.ingest_api = ingest_api
        self.archive_submission_url = None
        self.entity_url_map = {}
        self.types = {
            'sample': 'SAMPLE',
            'project': 'PROJECT',
            'study': 'STUDY',
            'sequencingExperiment': 'SEQUENCING_EXPERIMENT',
            'sequencingRun': 'SEQUENCING_RUN'
        }

    def create_archive_submission(self, archive_submission: ArchiveSubmission) -> dict:
        data = self._map_archive_submission(archive_submission)

        ingest_archive_submission = self.ingest_api.create_archive_submission(data)
        self.archive_submission_url = ingest_archive_submission['_links']['self']['href']
        return ingest_archive_submission

    def update_archive_submission(self, archive_submission: ArchiveSubmission) -> dict:
        data = self._map_archive_submission(archive_submission)
        ingest_archive_submission = self.ingest_api.patch(self.archive_submission_url, data)
        self.archive_submission_url = ingest_archive_submission['_links']['self']['href']
        return ingest_archive_submission

    def patch_archive_submission(self, attr_map: dict) -> dict:
        update = attr_map
        ingest_archive_submission = self.ingest_api.patch(self.archive_submission_url, update)
        self.archive_submission_url = ingest_archive_submission['_links']['self']['href']
        return ingest_archive_submission

    def add_entity(self, entity: ArchiveEntity) -> dict:
        data = self._map_archive_entity(entity)
        ingest_entity = self.ingest_api.create_archive_entity(self.archive_submission_url, data)
        ingest_url = ingest_entity['_links']['self']['href']
        self.entity_url_map[entity.dsp_uuid] = ingest_url
        return ingest_entity

    def update_entities(self, entity_map: EntityMap):
        for entity in entity_map.get_entities():
            self.update_entity(entity)

    def update_entity(self, entity: ArchiveEntity) -> dict:
        data = self._map_archive_entity(entity)
        if self.entity_url_map.get(entity.dsp_uuid):
            ingest_entity_url = self.entity_url_map.get(entity.dsp_uuid)
        else:
            ingest_entity = self.find_entity(entity)
            ingest_entity_url = ingest_entity['_links']['self']['href']
        ingest_entity = self.ingest_api.patch(ingest_entity_url, data)
        return ingest_entity

    def find_entity(self, entity: ArchiveEntity) -> dict:
        return self.ingest_api.get_archive_entity_by_alias(entity.id)

    def set_submission_as_archived(self, archive_submission: ArchiveSubmission):
        dsp_uuid = archive_submission.dsp_uuid
        archive_submission = self.ingest_api.get_archive_submission_by_dsp_uuid(dsp_uuid)
        ingest_submission_uuid = archive_submission['submissionUuid']
        ingest_submission = self.ingest_api.get_submission_by_uuid(ingest_submission_uuid)

        if ingest_submission['_links'].get('archived'):
            set_archived_link = ingest_submission['_links']['archived']['href']
            self.ingest_api.put(set_archived_link)

    def _map_archive_submission(self, archive_submission: ArchiveSubmission):
        data = {
            'dspUuid': archive_submission.dsp_uuid,
            'dspUrl': archive_submission.dsp_url,
            'fileUploadPlan': {"jobs": archive_submission.file_upload_info},
            'errors': self._map_errors(archive_submission.errors)
        }
        return self._clean_data(data)

    def _map_archive_entity(self, entity: ArchiveEntity):
        data = {
            'type': self.types[entity.archive_entity_type],
            'alias': entity.id,
            'dspUuid': entity.dsp_uuid,
            'dspUrl': entity.dsp_url,
            'accession': entity.accession,
            'conversion': entity.conversion,
            'metadataUuids': entity.metadata_uuids,
            'accessionedMetadataUuids': entity.accessioned_metadata_uuids,
            'errors': self._map_errors(entity.errors)
        }

        return self._clean_data(data)

    def _clean_data(self, data: dict):
        return {attr: val for attr, val in data.items() if val is not None}

    def _map_errors(self, errors: List['Error']):
        return [{
            'errorCode': error.error_code,
            'message': error.message,
            'details': error.details
        } for error in errors]
