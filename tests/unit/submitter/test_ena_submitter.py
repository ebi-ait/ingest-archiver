import unittest
from os.path import dirname

from assertpy import assert_that
from mock import MagicMock

from archiver import ConvertedEntity
from hca.submission import HcaSubmission
from submitter.ena_study import EnaSubmitter
from tests.unit.submitter import create_archive_response
from tests.unit.utils import make_ingest_entity, random_id, random_uuid


class TestEnaSubmitter(unittest.TestCase):
    def setUp(self) -> None:
        self.archive_client = MagicMock()
        self.converter = MagicMock()
        self.updater = MagicMock()
        self.empty_study = {}
        self.converter.convert = MagicMock(return_value=self.empty_study)
        self.submitter_service = MagicMock()
        self.submitter = EnaSubmitter(self.archive_client, self.updater)
        self.submitter.converter = self.converter
        self.submitter.converter.init_ena_set()
        # self.submitter._submit_to_archive = MagicMock()
        self.submission = HcaSubmission()
        self.ARCHIVE_TYPE = 'ENA'
        self.entity_type = 'projects'
        self.ena_study_accession = 'PRJ12345'
        # self.error_key = ERROR_KEY
        self.additional_parameters = {}

        self.project_uuid = random_uuid()
        self.entity = self.submission.map_ingest_entity(
            make_ingest_entity(self.entity_type, random_id(), self.project_uuid)
        )

    def test_when_convert_project_without_accession_returns_project_for_creation(self):
        converted_projects = \
            self.submitter.convert_all_entities(self.submission, self.ARCHIVE_TYPE, self.additional_parameters)

        assert_that(len(converted_projects)).is_equal_to(1)

        converted_entity: ConvertedEntity = converted_projects[0]
        is_create = not converted_entity.is_update

        assert_that(is_create).is_true()

    def test_when_convert_project_with_accession_returns_project_for_update(self):
        self.entity.add_accession(self.ARCHIVE_TYPE, self.ena_study_accession)

        converted_projects = \
            self.submitter.convert_all_entities(self.submission, self.ARCHIVE_TYPE, self.additional_parameters)

        assert_that(len(converted_projects)).is_equal_to(1)

        converted_entity: ConvertedEntity = converted_projects[0]
        is_update = converted_entity.is_update

        assert_that(is_update).is_true()

    def test_when_send_entities_to_archive_get_back_correct_archive_response(self):
        is_update = False
        converted_ena_study = [
            ConvertedEntity(data=self.empty_study, hca_entity_type=self.entity_type, is_update=is_update)
        ]
        self.archive_client.send_submission = MagicMock(side_effect=[
            bytes(
                self.__get_expected_payload('/../../resources/ena_receipt.xml'),
                'utf-8'
            )
        ])
        archive_responses = self.submitter.send_all_entities(converted_ena_study, self.ARCHIVE_TYPE)

        assert_that(len(archive_responses)).is_equal_to(len(converted_ena_study))
        for archive_response in archive_responses:
            assert_that(archive_response.data).is_not_none()
            assert_that(archive_response.entity_type).is_equal_to(self.entity_type)
            assert_that(archive_response.is_update).is_equal_to(is_update)

    def test_processing_archive_response_from_project_creation_add_result_for_created(self):
        payload = {'accession': 'ERP12345', 'uuid': self.project_uuid}
        archive_response = create_archive_response(payload, self.entity_type)
        archive_responses = [archive_response]
        processed_responses_from_archive =\
            self.submitter.process_responses(self.submission, archive_responses, '', self.ARCHIVE_TYPE)

        assert_that(len(processed_responses_from_archive)).is_equal_to(1)
        assert_that(processed_responses_from_archive).contains('CREATED')
        assert_that(processed_responses_from_archive.get('CREATED')).is_equal_to(archive_responses)

    def test_processing_archive_response_from_project_update_add_result_for_updated(self):
        payload = {'accession': 'ERP12345', 'uuid': self.project_uuid}
        archive_response = create_archive_response(payload, self.entity_type, is_update=True)
        archive_responses = [archive_response]
        processed_responses_from_archive =\
            self.submitter.process_responses(self.submission, archive_responses, '', self.ARCHIVE_TYPE)

        assert_that(len(processed_responses_from_archive)).is_equal_to(1)
        assert_that(processed_responses_from_archive).contains('UPDATED')
        assert_that(processed_responses_from_archive.get('UPDATED')).is_equal_to(archive_responses)

    def test_processing_archive_response_from_sample_update_add_result_for_updated(self):
        payload = {'error_messages': ['Dummy error message'], 'accession': 'ERP12345', 'uuid': self.project_uuid}
        archive_response = \
            create_archive_response(payload, self.entity_type, is_update=True)
        archive_responses = [archive_response]
        processed_responses_from_archive =\
            self.submitter.process_responses(self.submission, archive_responses, '', self.ARCHIVE_TYPE)

        assert_that(len(processed_responses_from_archive)).is_equal_to(1)
        assert_that(processed_responses_from_archive).contains('ERRORED')
        assert_that(processed_responses_from_archive.get('ERRORED')).is_equal_to(archive_responses)

    @staticmethod
    def __get_expected_payload(filename: str):
        with open(dirname(__file__) + filename) as file:
            return file.read()


if __name__ == '__main__':
    unittest.main()
