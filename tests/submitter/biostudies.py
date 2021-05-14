import unittest
from typing import List

from mock import MagicMock, call

from hca.submission import HcaSubmission, Entity
from submitter.biostudies import BioStudiesSubmitter
from tests.utils import make_ingest_entity, random_id, random_uuid


class TestBioSamplesSubmitter(unittest.TestCase):
    def setUp(self) -> None:
        self.biostudies = MagicMock()
        self.biostudies.send_project = MagicMock()
        self.converter = MagicMock()
        self.empty_project = {}
        self.converter.convert = MagicMock(return_value=self.empty_project)
        self.submitter = BioStudiesSubmitter(self.biostudies, self.converter)
        self.submission = HcaSubmission()
        self.biostudies_accession = 'BST_ACC_12345'

    def test_submit_project_converts_and_sends_project(self):
        # Given
        test_case = self.submission.map_ingest_entity(
            make_ingest_entity('projects', random_id(), random_uuid())
        )
        # When
        result = self.submitter.send_project(test_case)

        # Then
        self.converter.convert.assert_called_once_with(test_case.attributes)
        self.biostudies.send_submission.assert_called_once_with(self.empty_project)
        self.assertEqual('UPDATED', result)

    def test_submit_project_return_creation(self):
        # Given
        self.biostudies.send_submission = MagicMock(return_value={'accession': self.biostudies_accession})
        test_case = self.submission.map_ingest_entity(make_ingest_entity('projects', random_id(), random_uuid()))
        # When
        result = self.submitter.send_project(test_case)
        # Then
        self.assertEqual('CREATED', result)

    def test_submit_project_return_error(self):
        # Given
        error_msg = f'TestCaseError{random_id(3)}'
        self.biostudies.send_submission = MagicMock(side_effect=Exception(error_msg))
        test_case = self.submission.map_ingest_entity(
            make_ingest_entity('projects', random_id(), random_uuid()))
        # When
        result = self.submitter.send_project(test_case)
        # Then
        self.assertEqual('ERRORED', result)
        self.assertDictEqual(test_case.get_errors(), {'content.project_core.biostudies_accession': [f'BioStudies Error: {error_msg}']})

    def test_send_all_projects_sorts_projects_into_results(self):
        # Given
        self.submitter.send_project = MagicMock(side_effect=['UPDATED', 'CREATED', 'ERRORED'])
        projects = self.map_random_projects(self.submission, 3)
        calls = []
        call_count = 0
        for entity in projects:
            call_count += 1
            calls.append(call(entity))

        # When
        result = self.submitter.send_all_projects(self.submission)

        # Then
        self.submitter.send_project.assert_has_calls(calls, any_order=True)
        self.assertEqual(call_count, self.submitter.send_project.call_count)
        self.assertEqual(1, len(result['UPDATED']))
        self.assertEqual(1, len(result['CREATED']))
        self.assertEqual(1, len(result['ERRORED']))

    @staticmethod
    def map_random_projects(submission: HcaSubmission, entity_count: int) -> List[Entity]:
        projects = []
        for i in range(0, entity_count):
            projects.append(
                submission.map_ingest_entity(
                    make_ingest_entity('projects', random_id(), random_uuid())
                )
            )
        return projects


if __name__ == '__main__':
    unittest.main()
