import unittest
from typing import List

from mock import MagicMock, call

from hca.submission import HcaSubmission, Entity
from submitter.base import UPDATED_ENTITY, CREATED_ENTITY, ERRORED_ENTITY
from submitter.biostudies import BioStudiesSubmitter, ERROR_KEY
from tests.unit.utils import make_ingest_entity, random_id, random_uuid


class TestBioStudiesSubmitter(unittest.TestCase):
    def setUp(self) -> None:
        self.archive_client = MagicMock()
        self.converter = MagicMock()
        self.empty_project = {}
        self.converter.convert = MagicMock(return_value=self.empty_project)
        self.submitter_service = MagicMock()
        self.submitter = BioStudiesSubmitter(self.archive_client, self.converter, self.submitter_service)
        self.submitter._submit_to_archive = MagicMock()
        self.submission = HcaSubmission()
        self.archive_type = 'BioStudies'
        self.entity_type = 'projects'
        self.biostudies_accession = 'BST_ACC_12345'
        self.error_key = ERROR_KEY

    def test_submit_project_converts_and_sends_project(self):
        # Given
        test_case = self.submission.map_ingest_entity(
            make_ingest_entity(self.entity_type, random_id(), random_uuid())
        )
        # When
        result, accession = self.submitter.send_entity(test_case, self.archive_type, self.error_key)
        other_attributes = {}

        # Then
        self.converter.convert.assert_called_once_with(test_case.attributes, other_attributes)
        self.submitter._submit_to_archive.assert_called_once_with(self.empty_project)
        self.assertEqual(UPDATED_ENTITY, result)

    def test_submit_project_return_creation(self):
        # Given
        self.submitter._submit_to_archive = MagicMock(return_value={'accession': self.biostudies_accession})
        test_case = self.submission.map_ingest_entity(make_ingest_entity(self.entity_type, random_id(), random_uuid()))
        # When
        result, accession = self.submitter.send_entity(test_case, self.archive_type, self.error_key)
        # Then
        self.assertEqual(CREATED_ENTITY, result)

    def test_submit_project_return_error(self):
        # Given
        error_msg = f'TestCaseError{random_id(3)}'
        self.submitter._submit_to_archive = MagicMock(side_effect=Exception(error_msg))
        test_case = self.submission.map_ingest_entity(
            make_ingest_entity(self.entity_type, random_id(), random_uuid()))
        # When
        result, accession = self.submitter.send_entity(test_case, self.archive_type, self.error_key)
        # Then
        self.assertEqual(ERRORED_ENTITY, result)
        self.assertDictEqual(test_case.get_errors(), {self.error_key: [f'BioStudies Error: {error_msg}']})

    def test_send_all_projects_sorts_projects_into_results(self):
        # Given
        self.submitter.send_entity = MagicMock(side_effect=[
            [UPDATED_ENTITY, "1234"], [CREATED_ENTITY, "5678"], [ERRORED_ENTITY, "9012"]
        ])
        entities = self.map_random_entities(self.submission, self.entity_type, 3)
        calls = []
        call_count = 0
        for entity in entities:
            call_count += 1
            calls.append(call(entity, self.archive_type, self.error_key, None))

        # When
        result, accessions = self.submitter.send_all_projects(self.submission)

        # Then
        self.submitter.send_entity.assert_has_calls(calls, any_order=True)
        self.assertEqual(call_count, self.submitter.send_entity.call_count)
        self.assertEqual(1, len(result[UPDATED_ENTITY]))
        self.assertEqual(1, len(result[CREATED_ENTITY]))
        self.assertEqual(1, len(result[ERRORED_ENTITY]))

    @staticmethod
    def map_random_entities(submission: HcaSubmission, entity_type, entity_count: int) -> List[Entity]:
        projects = []
        for i in range(0, entity_count):
            projects.append(
                submission.map_ingest_entity(
                    make_ingest_entity(entity_type, random_id(), random_uuid())
                )
            )
        return projects


if __name__ == '__main__':
    unittest.main()
