import json
import unittest
from os.path import dirname
from typing import List

from assertpy import assert_that
from mock import MagicMock

from archiver import ConvertedEntity
from hca.submission import HcaSubmission, Entity
from submitter.biostudies import BioStudiesSubmitter
from tests.unit.submitter import create_archive_response
from tests.unit.utils import make_ingest_entity, random_id, random_uuid


class TestBioStudiesSubmitter(unittest.TestCase):
    def setUp(self) -> None:
        self.archive_client = MagicMock()
        self.converter = MagicMock()
        self.updater = MagicMock()
        self.empty_project = {}
        self.converter.convert = MagicMock(return_value=self.empty_project)
        self.submitter_service = MagicMock()
        self.submitter = BioStudiesSubmitter(self.archive_client, self.converter, self.submitter_service, self.updater)
        self.submission = HcaSubmission()
        self.ARCHIVE_TYPE = 'BioStudies'
        self.entity_type = 'projects'
        self.biostudies_accession = 'BST_ACC_12345'
        self.additional_parameters = {}

        self.entity = self.submission.map_ingest_entity(
            make_ingest_entity(self.entity_type, random_id(), random_uuid())
        )

    def test_when_convert_project_without_accession_returns_project_for_creation(self):
        converted_projects = \
            self.submitter.convert_all_entities(self.submission, self.ARCHIVE_TYPE, self.additional_parameters)

        assert_that(len(converted_projects)).is_equal_to(1)

        converted_entity: ConvertedEntity = converted_projects[0]
        is_create = not converted_entity.is_update

        assert_that(is_create).is_true()

    def test_when_convert_project_with_accession_returns_project_for_update(self):
        self.entity.add_accession(self.ARCHIVE_TYPE, self.biostudies_accession)

        converted_projects = \
            self.submitter.convert_all_entities(self.submission, self.ARCHIVE_TYPE, self.additional_parameters)

        assert_that(len(converted_projects)).is_equal_to(1)

        converted_entity: ConvertedEntity = converted_projects[0]
        is_update = converted_entity.is_update

        assert_that(is_update).is_true()

    def test_when_send_entities_to_archive_get_back_correct_archive_response(self):
        is_update = False
        converted_projects = [
            ConvertedEntity(data=self.empty_project, hca_entity_type=self.entity_type, is_update=is_update)
        ]
        self.archive_client.send_submission = MagicMock(side_effect=[
            'BSST-123'
        ])
        archive_responses = self.submitter.send_all_entities(converted_projects, self.ARCHIVE_TYPE)

        assert_that(len(archive_responses)).is_equal_to(len(converted_projects))
        for archive_response in archive_responses:
            assert_that(archive_response.data).is_not_none()
            assert_that(archive_response.entity_type).is_equal_to(self.entity_type)
            assert_that(archive_response.is_update).is_equal_to(is_update)

    def test_processing_archive_response_from_project_creation_add_result_for_created(self):
        payload = self.__get_expected_payload('/../../resources/expected_biostudies_payload.json')
        archive_response = create_archive_response(payload, self.entity_type)
        archive_responses = [archive_response]
        processed_responses_from_archive =\
            self.submitter.process_responses(self.submission, archive_responses, '', self.ARCHIVE_TYPE)

        assert_that(len(processed_responses_from_archive)).is_equal_to(1)
        assert_that(processed_responses_from_archive).contains('CREATED')
        assert_that(processed_responses_from_archive.get('CREATED')).is_equal_to(archive_responses)

    def test_processing_archive_response_from_sample_update_add_result_for_updated(self):
        payload = self.__get_expected_payload('/../../resources/expected_biostudies_payload.json')
        archive_response = create_archive_response(payload, self.entity_type, is_update=True)
        archive_responses = [archive_response]
        processed_responses_from_archive =\
            self.submitter.process_responses(self.submission, archive_responses, '', self.ARCHIVE_TYPE)

        assert_that(len(processed_responses_from_archive)).is_equal_to(1)
        assert_that(processed_responses_from_archive).contains('UPDATED')
        assert_that(processed_responses_from_archive.get('UPDATED')).is_equal_to(archive_responses)

    @staticmethod
    def __get_expected_payload(file_path: str):
        with open("{0}{1}".format(dirname(__file__), file_path)) as file:
            expected_payload = json.load(file)
        return expected_payload

    # def test_submit_project_converts_and_sends_project(self):
    #     # Given
    #     test_case = self.submission.map_ingest_entity(
    #         make_ingest_entity(self.entity_type, random_id(), random_uuid())
    #     )
    #     # When
    #     result, accession = self.submitter.send_entity(test_case, self.archive_type, self.error_key)
    #     other_attributes = {}
    #
    #     # Then
    #     self.converter.convert.assert_called_once_with(test_case.attributes, other_attributes)
    #     self.submitter._submit_to_archive.assert_called_once_with(self.empty_project)
    #     self.assertEqual(UPDATED_ENTITY, result)
    #
    # def test_submit_project_return_creation(self):
    #     # Given
    #     self.submitter._submit_to_archive = MagicMock(return_value={'accession': self.biostudies_accession})
    #     test_case = self.submission.map_ingest_entity(make_ingest_entity(self.entity_type, random_id(), random_uuid()))
    #     # When
    #     result, accession = self.submitter.send_entity(test_case, self.archive_type, self.error_key)
    #     # Then
    #     self.assertEqual(CREATED_ENTITY, result)
    #
    # def test_submit_project_return_error(self):
    #     # Given
    #     error_msg = f'TestCaseError{random_id(3)}'
    #     self.submitter._submit_to_archive = MagicMock(side_effect=Exception(error_msg))
    #     test_case = self.submission.map_ingest_entity(
    #         make_ingest_entity(self.entity_type, random_id(), random_uuid()))
    #     # When
    #     result, accession = self.submitter.send_entity(test_case, self.archive_type, self.error_key)
    #     # Then
    #     self.assertEqual(ERRORED_ENTITY, result)
    #     self.assertDictEqual(test_case.get_errors(), {self.error_key: [f'BioStudies Error: {error_msg}']})
    #
    # def test_send_all_projects_sorts_projects_into_results(self):
    #     # Given
    #     self.submitter.send_entity = MagicMock(side_effect=[
    #         [UPDATED_ENTITY, "1234"], [CREATED_ENTITY, "5678"], [ERRORED_ENTITY, "9012"]
    #     ])
    #     entities = self.map_random_entities(self.submission, self.entity_type, 3)
    #     calls = []
    #     call_count = 0
    #     for entity in entities:
    #         call_count += 1
    #         calls.append(call(entity, self.archive_type, self.error_key, {}))
    #
    #     # When
    #     result, accessions = self.submitter.send_all_projects(self.submission)
    #
    #     # Then
    #     self.submitter.send_entity.assert_has_calls(calls, any_order=True)
    #     self.assertEqual(call_count, self.submitter.send_entity.call_count)
    #     self.assertEqual(1, len(result[UPDATED_ENTITY]))
    #     self.assertEqual(1, len(result[CREATED_ENTITY]))
    #     self.assertEqual(1, len(result[ERRORED_ENTITY]))

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
