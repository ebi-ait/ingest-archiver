import logging
from copy import deepcopy
from typing import Tuple

from requests.exceptions import HTTPError
from assertpy import assert_warn
from biosamples_v4.api import Client as BioSamplesClient
from ingest.api.ingestapi import IngestApi
from submission_broker.services.biosamples import BioSamples

from converter.biosamples import BioSamplesConverter
from .loader import DuplicateLoader
from .submission import DuplicateSubmission, HcaSubmission


class DuplicateArchiver:
    def __init__(self, ingest: IngestApi, biosamples: BioSamplesClient, test_biosamples: BioSamples, converter: BioSamplesConverter):
        self.ingest = ingest
        self.loader = DuplicateLoader(ingest)
        self.read_biosamples = biosamples
        self.converter = converter
        self.write_biosamples = test_biosamples
        logger = logging.getLogger('biosample_comparisons')
        logger.setLevel(logging.INFO)
        fh = logging.FileHandler("biosample_comparisons.log")
        fh.setLevel(logging.INFO)
        logger.addHandler(fh)

    def compare_duplicate_biosample(self, biosamples_accession: str, ignored_keys):
        submission, biomaterial_uuid, project_uuid = self.__load_project_and_biomaterial(biosamples_accession)
        self.__send_biosample(submission, biomaterial_uuid, project_uuid)
        self.__log_comparison(submission, biomaterial_uuid, ignored_keys)

    def compare_duplicate_project(self, project_uuid: str, ignored_keys):
        submission = self.loader.duplicate_project(project_uuid)
        for biomaterial_uuid, biosamples_accession in submission.old_accessions['BioSamples'].items():
            biosample = self.read_biosamples.fetch_sample(biosamples_accession)
            submission.biosamples.setdefault(biomaterial_uuid, {})['old'] = biosample
            self.__send_biosample(submission, biomaterial_uuid, project_uuid)
            self.__log_comparison(submission, biomaterial_uuid, ignored_keys)

    def __load_project_and_biomaterial(self, biosamples_accession: str) -> Tuple[DuplicateSubmission, str, str]:
        # Restricted Loader that only loads the one project and one biomaterial rather than loading the whole project.
        submission = DuplicateSubmission()
        biosample = self.read_biosamples.fetch_sample(biosamples_accession)
        biomaterial_uuid = biosample.get('characteristics', {}).get('HCA Biomaterial UUID', [{}])[0].get('text', '')
        biomaterial = self.ingest.get_entity_by_uuid('biomaterials', biomaterial_uuid)
        biomaterial_entity = submission.map_ingest_entity(biomaterial)
        project_url = self.ingest.get_link_from_resource(biomaterial, 'project')
        response = self.ingest.get(project_url)
        response.raise_for_status()
        project = response.json()
        project_uuid = project.get('uuid', {}).get('uuid')
        project_entity = submission.map_ingest_entity(project)
        submission.link_entities(project_entity, biomaterial_entity)
        submission.biosamples.setdefault(biomaterial_uuid, {})['old'] = biosample
        return submission, biomaterial_uuid, project_uuid

    # Todo: Refactor Entity to allow storage of response object so that we can use the real submitter here
    def __send_biosample(self, submission: DuplicateSubmission, biomaterial_uuid: str, project_uuid: str):
        project_release_date = self.__get_project_release_date(submission, project_uuid)
        biomaterial = submission.get_entity_by_uuid('biomaterials', biomaterial_uuid)
        sample = self.converter.convert(biomaterial.attributes, release_date=project_release_date)
        try:
            biosample = self.write_biosamples.send_sample(sample)
            submission.biosamples.setdefault(biomaterial_uuid, {})['new'] = biosample
        except HTTPError:
            payload = self.write_biosamples.encoder.default(sample)
            submission.biosamples.setdefault(biomaterial_uuid, {})['new'] = payload

    @staticmethod
    def __log_comparison(submission: DuplicateSubmission, biomaterial_uuid: str, ignored_keys):
        old_sample = deepcopy(submission.biosamples.get(biomaterial_uuid, {}).get('old', {}))
        new_sample = deepcopy(submission.biosamples.get(biomaterial_uuid, {}).get('new', {}))
        logger = logging.getLogger('biosample_comparisons')
        logger.info(f"Comparing Biomaterial UUID: {biomaterial_uuid}, original: {old_sample.get('accession', 'NoOriginal')}, new {new_sample.get('accession', 'SubmissionFailed')}")
        for key in ignored_keys:
            if key in old_sample:
                old_sample.pop(key)
            if key in new_sample:
                new_sample.pop(key)
        assert_warn(old_sample, logger=logger).is_equal_to(new_sample, ignore=ignored_keys)

    @staticmethod
    def __get_project_release_date(submission: HcaSubmission, project_uuid: str = None) -> str:
        if project_uuid:
            return submission.get_entity_by_uuid('projects', project_uuid).attributes.get('releaseDate')
        projects = submission.get_entities('projects')
        for project in projects:
            if 'releaseDate' in project.attributes:
                return project.attributes['releaseDate']
