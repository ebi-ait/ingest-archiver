from typing import List

from .errors import IngestArchiveError


class IngestArchiveEntity:
    def __init__(self):
        self.data = {}
        self.metadata_uuids = None
        self.accessioned_metadata_uuids = None
        self.conversion = {}
        self.errors: List[IngestArchiveError] = []
        self.warnings = []
        self.id = None
        self.archive_entity_type = None
        self.accession = None
        self.links = {}
        self.manifest_id = None

    def __str__(self):
        return str(vars(self))

    def add_error(self, error_code, message, details=None):
        self.errors.append(IngestArchiveError(error_code, message, details))

    @staticmethod
    def map_from_report(report_id, report_entity):
        entity = IngestArchiveEntity()
        entity.id = report_id
        entity.archive_entity_type = report_entity['type']
        entity.conversion = report_entity['converted_data']
        entity.accession = report_entity['accession']
        entity.errors = report_entity['errors']
        entity.warnings = report_entity['warnings']
        return entity

    @staticmethod
    def map_from_ingest_entity(ingest_entity: dict):
        entity = IngestArchiveEntity()
        entity.id = ingest_entity['alias']
        entity.archive_entity_type = ingest_entity.get('type')
        entity.conversion = ingest_entity['conversion']
        entity.accession = ingest_entity['accession']
        entity.errors = ingest_entity['errors']
        entity.metadata_uuids = ingest_entity['metadataUuids']
        entity.accessioned_metadata_uuids = ingest_entity['accessionedMetadataUuids']
        return entity

