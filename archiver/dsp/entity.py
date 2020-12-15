from archiver.entity import IngestArchiveEntity
from .errors import IngestDspError


class IngestDspEntity(IngestArchiveEntity):
    dsp_json = None
    dsp_url = None
    dsp_uuid = None
    dsp_current_version = None

    @staticmethod
    def map_from_ingest_entity(ingest_entity: dict):
        entity = IngestDspEntity()
        entity.id = ingest_entity['alias']
        entity.archive_entity_type = ingest_entity.get('type')
        entity.conversion = ingest_entity['conversion']
        entity.accession = ingest_entity['accession']
        entity.errors = ingest_entity['errors']
        entity.metadata_uuids = ingest_entity['metadataUuids']
        entity.accessioned_metadata_uuids = ingest_entity['accessionedMetadataUuids']
        entity.dsp_url = ingest_entity['dspUrl']
        entity.dsp_uuid = ingest_entity['dspUuid']
        return entity

    def add_error(self, error_code, message, details=None):
        self.errors.append(IngestDspError(error_code, message, details))
