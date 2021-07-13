from typing import List, Union

from ingest.api.ingestapi import IngestApi
from hca.submission import HcaSubmission, Entity, HandleCollision


class HcaLoader:
    def __init__(self, ingest: IngestApi):
        self.__ingest = ingest

    def get_project(self, project_uuid: str) -> HcaSubmission:
        hca_submission = HcaSubmission(HandleCollision.OVERWRITE)
        self._map_project(hca_submission, project_uuid)
        return hca_submission

    def get_submission(self, submission_uuid: str) -> HcaSubmission:
        hca_submission = HcaSubmission(HandleCollision.OVERWRITE)
        self._map_submission(hca_submission, submission_uuid)
        return hca_submission

    def _map_project(self, hca_submission, project_uuid):
        project_type = 'projects'
        project = self._map_entity(hca_submission, project_type, project_uuid)
        submission_type = 'submissionEnvelopes'
        self.__map_link_type_to_link_names(hca_submission, project, submission_type)
        for submission_entity in hca_submission.get_entities(submission_type):
            self.__map_submission_manifests(hca_submission, submission_entity)

    def _map_submission(self, hca_submission, submission_uuid):
        submission_type = 'submissionEnvelopes'
        submission_entity = self._map_entity(hca_submission, submission_type, submission_uuid)
        self.__map_submission_manifests(hca_submission, submission_entity)

    def __map_submission_manifests(self, hca_submission: HcaSubmission, submission_entity: Entity):
        manifest_type = 'bundleManifests'
        self.__map_link_type_to_link_names(hca_submission, submission_entity, manifest_type)
        for manifest_entity in hca_submission.get_entities(manifest_type):
            self.__map_manifest_content(hca_submission, manifest_entity)

    def _map_entity(self, submission: HcaSubmission, entity_type: str, entity_uuid: str) -> Entity:
        entity = submission.get_entity_by_uuid(entity_type, entity_uuid)
        if not entity:
            entity_attributes = self.__ingest.get_entity_by_uuid(entity_type, entity_uuid)
            entity = submission.map_ingest_entity(entity_attributes)
            self.__add_related_entities(submission, entity)
        return entity

    def __add_related_entities(self, submission: HcaSubmission, entity: Entity):
        entity_type = entity.identifier.entity_type
        if entity_type == 'biomaterials' or entity_type == 'files':
            self.__map_link_type_to_link_names(submission, entity, link_type='processes', link_names=['inputToProcesses', 'derivedByProcesses'])
        elif entity_type == 'processes':
            self.__map_link_type_to_link_names(submission, entity, 'protocols')
            self.__map_link_type_to_link_names(submission, entity, link_type='biomaterials', link_names=['inputBiomaterials', 'derivedBiomaterials'])
            self.__map_link_type_to_link_names(submission, entity, link_type='files', link_names=['inputFiles', 'derivedFiles'])

    def __map_link_type_to_link_names(self, submission: HcaSubmission,
                                      entity: Entity,
                                      link_type: str,
                                      link_names: Union[str, List[str]] = None):
        if not link_names:
            link_names = link_type
        if type(link_names) == str:
            link_names = [link_names]
        for link_name in link_names:
            self.__map_related_entities(submission, entity, link_type, link_name)

    def __map_related_entities(self, submission: HcaSubmission, entity: Entity, related_entity_type: str, link_name):
        related_entities = self.__ingest.get_related_entities(link_name, entity.attributes, related_entity_type)
        for entity_attributes in related_entities:
            in_cache = submission.contains_entity(entity_attributes)
            related_entity = submission.map_ingest_entity(entity_attributes)
            if not in_cache:
                self.__add_related_entities(submission, related_entity)
            submission.link_entities(entity, related_entity)

    def __map_manifest_content(self, submission: HcaSubmission, manifest: Entity):
        self.__map_bundle_manifest_relations(submission, manifest, 'projects', 'fileProjectMap')
        self.__map_bundle_manifest_relations(submission, manifest, 'biomaterials', 'fileBiomaterialMap')
        self.__map_bundle_manifest_relations(submission, manifest, 'protocols', 'fileProtocolMap')
        self.__map_bundle_manifest_relations(submission, manifest, 'processes', 'fileProcessMap')
        self.__map_bundle_manifest_relations(submission, manifest, 'files', 'fileFilesMap')

    def __map_bundle_manifest_relations(self, submission: HcaSubmission, manifest: Entity, entity_type, manifest_key):
        for uuid in manifest.attributes.get(manifest_key, {}).keys():
            entity = self._map_entity(submission, entity_type, uuid)
            submission.link_entities(manifest, entity)
