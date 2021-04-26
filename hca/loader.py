from ingest.api.ingestapi import IngestApi
from submission_broker.submission.entity import Entity

from hca.submission import HcaSubmission


class HcaLoader:
    def __init__(self, ingest: IngestApi):
        self.ingest = ingest

    def map_project(self, project_uuid: str):
        hca_submission = HcaSubmission()
        project_type = 'projects'
        project = self.__map_entity(hca_submission, project_type, project_uuid)
        submission_type = 'submissionEnvelopes'
        self.__map_related_entities(hca_submission, project, submission_type)
        for submission_entity in hca_submission.get_entities(submission_type):
            self.__map_submission_manifests(hca_submission, submission_entity)
        return hca_submission

    def map_submission(self, submission_uuid: str):
        hca_submission = HcaSubmission()
        submission_type = 'submissionEnvelopes'
        submission_entity = self.__map_entity(hca_submission, submission_type, submission_uuid)
        self.__map_submission_manifests(hca_submission, submission_entity)
        return hca_submission

    def __map_submission_manifests(self, hca_submission: HcaSubmission, submission_entity: Entity):
        manifest_type = 'bundleManifests'
        self.__map_related_entities(hca_submission, submission_entity, manifest_type)
        for manifest_entity in hca_submission.get_entities(manifest_type):
            self.__map_manifest_content(hca_submission, manifest_entity.attributes)

    def __map_entity(self, submission: HcaSubmission, entity_type: str, entity_uuid: str) -> Entity:
        entity = submission.get_entity_from_uuid(entity_type, entity_uuid)
        if entity:
            return entity
        entity_attributes = self.ingest.get_entity_by_uuid(entity_type, entity_uuid)
        return submission.map_ingest_entity(entity_type, entity_attributes)

    def __map_related_entities(self, submission: HcaSubmission, entity: Entity, related_entity_type: str):
        related_entities = self.ingest.get_related_entities(related_entity_type, entity.attributes, related_entity_type)
        for entity_attributes in related_entities:
            related_entity = submission.map_ingest_entity(related_entity_type, entity_attributes)
            submission.link_entities(entity, related_entity)

    def __map_manifest_content(self, hca_submission: HcaSubmission, manifest: dict):
        # Save manifest content using self.__map_entity(hca_submission, entity_type, entity_uuid)
        #   This acts as a cache to reduce traffic
        #
        # entity_type is dependant on which key in the dictionary is inspected
        #   manifest.fileProjectMap = 'projects'
        #   manifest.fileBiomaterialMap = 'biomaterials'
        #   manifest.fileProtocolMap = 'protocols'
        #   manifest.fileFilesMap = 'files'
        #   manifest.fileProcessMap = 'processes'
        #   manifest.dataFiles = It's complicated
        pass

    def __link_submission_entities(self):
        # use self.ingest.get_related_entities to help here
        # for each 'processes' link to 'protocols', 'biomaterials' and 'files'
        # for each 'files' get linked 'processes'
        # for each 'biomaterials' get linked 'processes'
        pass
