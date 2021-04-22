import re

from submission_broker.submission.submission import Submission
from submission_broker.submission.entity import Entity
from ingest.api.ingestapi import IngestApi


class HcaSubmission:
    def __init__(self, ingest: IngestApi):
        self.ingest = ingest
        self.submission = Submission()
        self.uuid_map = {}

    def map_project(self, project_uuid: str):
        entity_type = 'projects'
        self.map_entity(entity_type, project_uuid)
        self.map_project_submissions(project_uuid)
        self.__link_submission_entities()

    def map_submission(self, submission_uuid):
        entity_type = 'submissionEnvelopes'
        self.map_entity(entity_type, submission_uuid)
        self.map_submission_manifests(submission_uuid)
        self.__link_submission_entities()

    def map_entity(self, entity_type: str, entity_uuid: str):
        if entity_uuid in self.uuid_map.get(entity_type, {}):
            return self.uuid_map[entity_type][entity_uuid]
        ingest_entity = self.ingest.get_entity_by_uuid(entity_type, entity_uuid)
        entity_id = HcaSubmission.__get_entity_id(ingest_entity, entity_type)
        self.uuid_map.setdefault(entity_type, {})[entity_uuid] = entity_id
        self.submission.map(entity_type, entity_id, ingest_entity)
        return entity_id

    def map_entities(self, entity_type: str, entities: list):
        for entity in entities:
            entity_id = HcaSubmission.__get_entity_id(entity, entity_type)
            entity_uuid = entity.get('uuid', {}).get('uuid', '')
            self.uuid_map.setdefault(entity_type, {})[entity_uuid] = entity_id
            self.submission.map(entity_type, entity_id, entity)

    def map_project_submissions(self, project_uuid: str):
        projects = 'projects'
        project_id = self.map_entity(projects, project_uuid)
        project = self.submission.get_entity(projects, project_id)

        entity_type = 'submissionEnvelopes'
        submissions = self.ingest.get_related_entities(entity_type, project, entity_type)
        self.map_entities(entity_type, submissions)
        for submission in submissions:
            submission_uuid = submission.get('uuid', {}).get('uuid', '')
            self.map_submission_manifests(submission_uuid)

    def map_submission_manifests(self, submission_uuid: str):
        submissions = 'submissionEnvelopes'
        submission_id = self.map_entity(submissions, submission_uuid)
        submission = self.submission.get_entity(submissions, submission_id)
        entity_type = 'bundleManifests'
        manifests = self.ingest.get_related_entities(entity_type, submission, entity_type)
        # Cannot self.map_entities because bundleManifests have not uuids
        for manifest in manifests:
            self.__map_manifest_content(manifest)

    def __map_manifest_content(self, manifest: dict):
        # Save manifest content using self.map_entity(entity_type, entity_uuid)
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

    @staticmethod
    def __get_entity_id(entity: dict, entity_type: str):
        entity_uri = HcaSubmission.__get_link(entity, 'self')
        id_match = re.search(f'/{entity_type}/' + r'(.*)$', entity_uri)
        entity_id = id_match.group(1) if id_match else ''
        return entity_id

    @staticmethod
    def __get_link(entity, link_name):
        link = entity['_links'][link_name]
        return link['href'].rsplit("{")[0] if link else ''

