import logging
from typing import List

from requests import HTTPError
from api.ingest import IngestAPI
from .entity_map import ArchiveEntityMap
from .entity import IngestArchiveEntity


class IngestAccession:
    def __init__(self, ingest_type, ingest_url, accession_id, accession_type=None):
        self.ingest_type = ingest_type
        self.ingest_url = ingest_url
        self.accession_id = accession_id
        if not accession_type:
            accession_type = ingest_type
        self.accession_type = accession_type


class Accessioner:
    def __init__(self, ingest_api: IngestAPI):
        self.ingest_api = ingest_api
        self.ARCHIVE_TO_INGEST_ENTITY_TYPE_MAP = {
            'project': 'project',
            'study': 'project',
            'sample': 'biomaterial',
            'sequencingExperiment': 'process',
            'sequencingRun': 'file'
        }

        self.ARCHIVE_ACCESSION_TYPE_MAP = {
            'project': 'project',
            'study': 'study',
            'sample': 'biomaterial',
            'sequencingExperiment': 'process',
            'sequencingRun': 'file'
        }

        self.PLURAL_INGEST_TYPE_MAP = {
            'project': 'projects',
            'biomaterial': 'biomaterials',
            'process': 'processes',
            'file': 'files'
        }

    # TODO needs to be updated!
    @staticmethod
    def is_metadata_accessioned(entity: IngestArchiveEntity):
        if entity.archive_entity_type != "sample":
            return False

        sample = entity.data.get("biomaterial")
        if sample:
            return ("biomaterial_core" in sample["content"]) and (
                "biosd_biomaterial" in sample["content"]["biomaterial_core"])

        return False

    @staticmethod
    def generate_patch(accession: IngestAccession, ingest_entity):
        entity_patch = {'content': ingest_entity['content']}
        if accession.accession_type == 'project':
            entity_patch['content']['biostudies_accessions'] = [accession.accession_id]
        elif accession.accession_type == 'study':
            entity_patch['content']['insdc_project_accessions'] = [accession.accession_id]
            # DSP returns study_accessions, but an error in HCA metadata requires we store them as project_accessions
            # Once this error is fixed we should also retrieve the project accession from ENA using the study accession
            # entity_patch['content']['insdc_study_accessions'] = [accession.accession_id]
        elif accession.accession_type == 'biomaterial':
            entity_patch['content']['biomaterial_core']['biosamples_accession'] = accession.accession_id
        elif accession.accession_type == 'process':
            entity_patch['content']['insdc_experiment'] = {
                'insdc_experiment_accession': accession.accession_id
            }
        elif accession.accession_type == 'file':
            entity_patch['content']['insdc_run_accessions'] = [accession.accession_id]

        # TODO IMPORTANT!!! How to make sure that patching won't invalidate the json

        return entity_patch

    def accession_entities(self, entity_map: ArchiveEntityMap):
        accessions = self.get_accessions_from_map(entity_map)

        self.ingest_api.entity_cache = {}
        for accession in accessions:
            entity_type, entity_id = self.ingest_api.entity_info_from_url(accession.ingest_url)
            ingest_entity = self.ingest_api.get_entity_by_id(entity_type, entity_id)
            entity_patch = Accessioner.generate_patch(accession, ingest_entity)
            try:
                self.ingest_api.patch_entity_by_id(entity_type, entity_id, entity_patch)
            except HTTPError:
                logging.error("Failed to send to ingest", HTTPError)

    def get_accessions_from_map(self, entity_map: ArchiveEntityMap) -> List[IngestAccession]:
        accessions: List[IngestAccession] = []
        for entity in entity_map.get_entities():
            accessions.extend(self.get_accessions_from_entity(entity))

        return accessions

    def get_ingest_entity_url(self, metadata_type, metadata_uuid):
        plural_type = self.PLURAL_INGEST_TYPE_MAP[metadata_type]
        entity = self.ingest_api.get_entity_by_uuid(plural_type, metadata_uuid)
        return entity['_links']['self']['href']

    def get_accessions_from_entity(self, entity: IngestArchiveEntity) -> List[IngestAccession]:
        accessions: List[IngestAccession] = []

        if entity.accession:
            ingest_entity_type = self.ARCHIVE_TO_INGEST_ENTITY_TYPE_MAP[entity.archive_entity_type]
            accession_type = self.ARCHIVE_ACCESSION_TYPE_MAP[entity.archive_entity_type]
            accessioned_metadata_uuids = entity.accessioned_metadata_uuids or []
            for ingest_entity_uuid in accessioned_metadata_uuids:
                entity_url = self.get_ingest_entity_url(ingest_entity_type, ingest_entity_uuid)
                accession = IngestAccession(ingest_entity_type, entity_url, entity.accession, accession_type)
                accessions.append(accession)

        return accessions

