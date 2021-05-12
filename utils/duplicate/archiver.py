import logging
from typing import Tuple

from biosamples_v4.api import Client as BioSamplesClient
from ingest.api.ingestapi import IngestApi
from submission_broker.submission.submission import Submission, Entity
from submission_broker.services.biosamples import BioSamples

from converter.biosamples import BioSamplesConverter
from .loader import DuplicateLoader
from .submission import DuplicateSubmission


class DuplicateArchiver:
    def __init__(self, ingest: IngestApi, biosamples: BioSamplesClient, test_biosamples: BioSamples, converter: BioSamplesConverter):
        self.ingest = ingest
        self.loader = DuplicateLoader(ingest)
        self.read_biosamples = biosamples
        self.converter = converter
        self.write_biosamples = test_biosamples

    def get_project_biomaterial_uuid(self, biosamples_accession: str) -> Tuple[str, str, dict]:
        biosample = self.read_biosamples.fetch_sample(biosamples_accession)
        biomaterial_uuid = biosample.get('characteristics', {}).get('HCA Biomaterial UUID', [{}])[0].get('text', '')
        logging.info(f'BioSample: {biosamples_accession} = Biomaterial: {biomaterial_uuid}')
        biomaterial = self.ingest.get_entity_by_uuid('biomaterials', biomaterial_uuid)
        project_url = self.ingest.get_link_from_resource(biomaterial, 'project')
        response = self.ingest.get(project_url)
        response.raise_for_status()
        project = response.json()
        project_uuid = project.get('uuid', {}).get('uuid')
        logging.info(f'Biomaterial: {biomaterial_uuid} = Project UUID: {project_uuid}')
        return project_uuid, biomaterial_uuid, biosample

    def load_project_from_biosample(self, biosamples_accession: str) -> Tuple[DuplicateSubmission, str]:
        project_uuid, biomaterial_uuid, biosample = self.get_project_biomaterial_uuid(biosamples_accession)
        submission = self.loader.duplicate_project(project_uuid)
        submission.biosamples.setdefault(biomaterial_uuid, {})['old'] = biosample
        return submission, biomaterial_uuid

    # Todo: Refactor Entity to allow storage of response object so that we can use the real submitter here
    def send_biosample(self, submission: DuplicateSubmission, biomaterial_uuid: str):
        project_release_date = self.__get_project_release_date_from_submission(submission)
        biomaterial = submission.get_entity_by_uuid('biomaterials', biomaterial_uuid)
        payload = self.converter.convert(biomaterial.attributes, release_date=project_release_date)
        biosample = self.write_biosamples.send_sample(payload)
        submission.biosamples.setdefault(biomaterial_uuid, {})['new'] = biosample
        return biosample

    @staticmethod
    def __get_project_release_date_from_submission(submission: Submission) -> str:
        projects = submission.get_entities('projects')
        for project in projects:
            if 'releaseDate' in project.attributes:
                return project.attributes['releaseDate']
