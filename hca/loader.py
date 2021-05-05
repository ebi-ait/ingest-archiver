from ingest.api.ingestapi import IngestApi
from hca.submission import HcaSubmission, Entity, HandleCollision


class HcaLoader:
    def __init__(self, ingest: IngestApi):
        self.__ingest = ingest

    def get_project(self, project_uuid: str) -> HcaSubmission:
        hca_submission = HcaSubmission(HandleCollision.OVERWRITE)
        project_type = 'projects'
        project = self.__map_entity(hca_submission, project_type, project_uuid)
        submission_type = 'submissionEnvelopes'
        self.__map_related_entities(hca_submission, project, submission_type)
        for submission_entity in hca_submission.get_entities(submission_type):
            self.__map_submission_manifests(hca_submission, submission_entity)
        return hca_submission

    def get_submission(self, submission_uuid: str) -> HcaSubmission:
        hca_submission = HcaSubmission(HandleCollision.OVERWRITE)
        submission_type = 'submissionEnvelopes'
        submission_entity = self.__map_entity(hca_submission, submission_type, submission_uuid)
        self.__map_submission_manifests(hca_submission, submission_entity)
        return hca_submission

    def __map_submission_manifests(self, hca_submission: HcaSubmission, submission_entity: Entity):
        manifest_type = 'bundleManifests'
        self.__map_related_entities(hca_submission, submission_entity, manifest_type)
        for manifest_entity in hca_submission.get_entities(manifest_type):
            self.__map_manifest_content(hca_submission, manifest_entity)

    def __map_entity(self, submission: HcaSubmission, entity_type: str, entity_uuid: str) -> Entity:
        entity = submission.get_entity_by_uuid(entity_type, entity_uuid)
        if not entity:
            entity_attributes = self.__ingest.get_entity_by_uuid(entity_type, entity_uuid)
            entity = submission.map_ingest_entity(entity_attributes)
            self.__add_related_entities(submission, entity)
        return entity

    def __add_related_entities(self, submission: HcaSubmission, entity: Entity):
        entity_type = entity.identifier.entity_type
        if entity_type == 'biomaterials' or entity_type == 'files':
            link_type = 'processes'
            self.__map_related_entities(submission, entity, link_type, 'inputToProcesses')
            self.__map_related_entities(submission, entity, link_type, 'derivedByProcesses')
        elif entity_type == 'processes':
            self.__map_related_entities(submission, entity, 'protocols')
            link_type = 'biomaterials'
            self.__map_related_entities(submission, entity, link_type, 'inputBiomaterials')
            self.__map_related_entities(submission, entity, link_type, 'derivedBiomaterials')
            link_type = 'files'
            self.__map_related_entities(submission, entity, link_type, 'inputFiles')
            self.__map_related_entities(submission, entity, link_type, 'derivedFiles')

    def __map_related_entities(self, submission: HcaSubmission, entity: Entity, related_entity_type: str, link_name: str = None):
        if not link_name:
            link_name = related_entity_type
        related_entities = self.__ingest.get_related_entities(link_name, entity.attributes, related_entity_type)
        for entity_attributes in related_entities:
            in_cache = submission.contains_entity(entity_attributes)
            related_entity = submission.map_ingest_entity(entity_attributes)
            if not in_cache:
                self.__add_related_entities(submission, related_entity)
            submission.link_entities(entity, related_entity)

    def __map_manifest_content(self, submission: HcaSubmission, manifest: Entity):
        for project_uuid in manifest.attributes.get('fileProjectMap', {}).keys():
            project = self.__map_entity(submission, 'projects', project_uuid)
            submission.link_entities(manifest, project)

        for biomaterial_uuid in manifest.attributes.get('fileBiomaterialMap', {}).keys():
            biomaterial = self.__map_entity(submission, 'biomaterials', biomaterial_uuid)
            submission.link_entities(manifest, biomaterial)

        for protocol_uuid in manifest.attributes.get('fileProtocolMap', {}).keys():
            protocol = self.__map_entity(submission, 'protocols', protocol_uuid)
            submission.link_entities(manifest, protocol)

        for process_uuid in manifest.attributes.get('fileProcessMap', {}).keys():
            process = self.__map_entity(submission, 'processes', process_uuid)
            submission.link_entities(manifest, process)

        data_file_map = {}
        for file_uuid in manifest.attributes.get('fileFilesMap', {}).keys():
            file = self.__map_entity(submission, 'files', file_uuid)
            submission.link_entities(manifest, file)
            data_file_uuid = file.attributes.get('dataFileUuid', '')
            data_file_map[data_file_uuid] = file
