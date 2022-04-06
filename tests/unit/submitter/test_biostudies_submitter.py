import json
import unittest
from os.path import dirname

from assertpy import assert_that
from mock import MagicMock

from archiver import ConvertedEntity
from hca.submission import HcaSubmission
from submitter.biostudies import BioStudiesSubmitter
from tests.unit.utils import make_ingest_entity, random_id, random_uuid


class TestBioStudiesSubmitter(unittest.TestCase):
    def setUp(self) -> None:
        self.archive_client = MagicMock()
        self.converter = MagicMock()
        self.updater = MagicMock()
        self.project = {
            'attributes': [
                {'name': 'Project Core - Project Short Name', 'value': 'GSE132065_BloodTimeHuman'},
                {'name': 'HCA Project UUID', 'value': '7988439a-2643-4ae9-8f84-74ea4fa62d90'}
            ]
        }
        self.converter.convert = MagicMock(return_value=self.project)
        self.submitter_service = MagicMock()
        self.submitter = BioStudiesSubmitter(self.archive_client, self.converter, self.submitter_service, self.updater)
        self.submission = HcaSubmission()
        self.ARCHIVE_TYPE = 'BioStudies'
        self.entity_type = 'projects'
        self.entity_schema_type = 'project'
        self.biostudies_accession = 'BST_ACC_12345'
        self.additional_parameters = {}

        self.entity = self.submission.map_ingest_entity(
            make_ingest_entity(self.entity_type, self.entity_schema_type, random_id(), random_uuid())
        )

    def test_when_convert_project_without_accession_returns_project_for_creation(self):
        converted_projects = \
            self.submitter.convert_all_entities(self.submission, self.ARCHIVE_TYPE, self.additional_parameters)

        assert_that(len(converted_projects)).is_equal_to(1)

        converted_entity: ConvertedEntity = converted_projects[0]
        is_create = not converted_entity.updated

        assert_that(is_create).is_true()

    def test_when_convert_project_with_accession_returns_project_for_update(self):
        self.entity.add_accession(self.ARCHIVE_TYPE, self.biostudies_accession)

        converted_projects = \
            self.submitter.convert_all_entities(self.submission, self.ARCHIVE_TYPE, self.additional_parameters)

        assert_that(len(converted_projects)).is_equal_to(1)

        converted_entity: ConvertedEntity = converted_projects[0]
        is_update = converted_entity.updated

        assert_that(is_update).is_true()

    def test_when_send_entities_to_archive_get_back_correct_archive_response(self):
        is_update = False
        converted_projects = [
            ConvertedEntity(data=self.project, hca_entity_type=self.entity_type, is_update=is_update)
        ]
        self.archive_client.send_submission = MagicMock(side_effect=[
            'BSST-123'
        ])
        archive_responses = self.submitter.send_all_entities(converted_projects, self.ARCHIVE_TYPE)

        assert_that(len(archive_responses)).is_equal_to(len(converted_projects))
        for archive_response in archive_responses:
            assert_that(archive_response.get('entity_type')).is_equal_to(self.entity_type)
            assert_that(archive_response.get('is_update')).is_equal_to(is_update)

    def test_when_accessions_are_empty_then_submission_wont_changed(self):
        biosample_accessions = []
        biostudies_accession = []
        ena_accessions = []

        self.submitter.update_submission_with_archive_accessions(
            biosample_accessions, biostudies_accession, ena_accessions)

        assert not self.submitter_service.get_biostudies_payload_by_accession.called

    @staticmethod
    def __get_expected_payload(file_path: str):
        with open("{0}{1}".format(dirname(__file__), file_path)) as file:
            expected_payload = json.load(file)
        return expected_payload


if __name__ == '__main__':
    unittest.main()
