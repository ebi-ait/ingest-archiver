import unittest

from assertpy import assert_that
from biosamples_v4.models import Sample
from mock.mock import MagicMock

from archiver import ConvertedEntity
from hca.submission import HcaSubmission
from submitter.biosamples import BioSamplesSubmitter
from tests.unit.submitter import create_archive_response
from tests.unit.utils import make_ingest_entity, random_id, random_uuid


class TestBioSamplesSubmitter(unittest.TestCase):

    def setUp(self) -> None:
        self.client = MagicMock()
        self.converter = MagicMock()
        self.empty_sample = Sample(ncbi_taxon_id=9606)
        self.sample1 = Sample(ncbi_taxon_id=9606, name='test1')
        self.sample2 = Sample(ncbi_taxon_id=9606, name='test2')
        self.converter.convert = MagicMock(return_value=self.empty_sample)
        self.updater = MagicMock()
        self.submitter_service = MagicMock()
        self.biosamples_submitter = \
            BioSamplesSubmitter(self.client, self.converter, self.submitter_service, self.updater)
        self.submission = HcaSubmission()
        self.ARCHIVE_TYPE = 'BioSamples'
        self.entity_type = 'biomaterials'
        self.entity_schema_type = 'biomaterial'
        self.entity = self.submission.map_ingest_entity(
            make_ingest_entity(self.entity_type, self.entity_schema_type, random_id(), random_uuid())
        )
        self.additional_parameters = {}

    def test_when_convert_biomaterials_without_accession_returns_sample_for_creation(self):
        converted_samples = \
            self.biosamples_submitter.convert_all_entities(self.submission, self.ARCHIVE_TYPE, self.additional_parameters)

        assert_that(len(converted_samples)).is_equal_to(1)

        converted_entity: ConvertedEntity = converted_samples[0]
        is_create = not converted_entity.is_update

        assert_that(converted_entity.data.accession).is_equal_to(None)
        assert_that(is_create).is_true()

    def test_when_convert_biomaterials_with_accession_returns_sample_for_update(self):
        accession = 'SAME1234'
        self.entity.add_accession(self.ARCHIVE_TYPE, accession)
        sample_with_accession = Sample(ncbi_taxon_id=9606, accession=accession)
        self.converter.convert = MagicMock(return_value=sample_with_accession)

        converted_samples = \
            self.biosamples_submitter.convert_all_entities(self.submission, self.ARCHIVE_TYPE, self.additional_parameters)

        assert_that(len(converted_samples)).is_equal_to(1)

        converted_entity: ConvertedEntity = converted_samples[0]
        is_update = converted_entity.is_update

        assert_that(converted_entity.data.accession).is_equal_to(accession)
        assert_that(is_update).is_true()

    def test_when_send_entities_to_archive_get_back_correct_archive_response(self):
        is_update = False
        converted_samples = [
            ConvertedEntity(data=self.empty_sample, hca_entity_type=self.entity_type, is_update=is_update),
            ConvertedEntity(data=self.sample1, hca_entity_type=self.entity_type, is_update=is_update),
            ConvertedEntity(data=self.sample2, hca_entity_type=self.entity_type, is_update=is_update)
        ]
        self.client.send_sample = MagicMock(side_effect=[
            {'name': 'empty', 'taxId': 9606},
            {'name': 'test1', 'taxId': 9606},
            {'name': 'test2', 'taxId': 9606}
        ])
        archive_responses = self.biosamples_submitter.send_all_entities(converted_samples, self.ARCHIVE_TYPE)

        assert_that(len(archive_responses)).is_equal_to(len(converted_samples))
        for archive_response in archive_responses:
            assert_that(archive_response.data).is_not_none()
            assert_that(archive_response.entity_type).is_equal_to(self.entity_type)
            assert_that(archive_response.is_update).is_equal_to(is_update)

    def test_processing_archive_response_from_sample_creation_add_result_for_created(self):
        archive_response_1 = create_archive_response({'name': 'empty', 'taxId': 9606, 'uuid': ''}, self.entity_type)
        archive_response_2 = create_archive_response({'name': 'test1', 'taxId': 9606, 'uuid': ''}, self.entity_type)
        archive_response_3 = create_archive_response({'name': 'test2', 'taxId': 9606, 'uuid': ''}, self.entity_type)
        archive_responses = [archive_response_1, archive_response_2, archive_response_3]
        processed_responses_from_archive =\
            self.biosamples_submitter.process_responses(self.submission, archive_responses, '', self.ARCHIVE_TYPE)

        assert_that(len(processed_responses_from_archive)).is_equal_to(1)
        assert_that(processed_responses_from_archive).contains('CREATED')
        assert_that(processed_responses_from_archive.get('CREATED')).is_equal_to(archive_responses)

    def test_processing_archive_response_from_sample_update_add_result_for_updated(self):
        archive_response_1 = create_archive_response({'name': 'empty', 'taxId': 9606, 'uuid': ''}, self.entity_type, is_update=True)
        archive_response_2 = create_archive_response({'name': 'test1', 'taxId': 9606, 'uuid': ''}, self.entity_type, is_update=True)
        archive_response_3 = create_archive_response({'name': 'test2', 'taxId': 9606, 'uuid': ''}, self.entity_type, is_update=True)
        archive_responses = [archive_response_1, archive_response_2, archive_response_3]
        processed_responses_from_archive =\
            self.biosamples_submitter.process_responses(self.submission, archive_responses, '', self.ARCHIVE_TYPE)

        assert_that(len(processed_responses_from_archive)).is_equal_to(1)
        assert_that(processed_responses_from_archive).contains('UPDATED')
        assert_that(processed_responses_from_archive.get('UPDATED')).is_equal_to(archive_responses)

    def test_processing_archive_response_from_sample_update_add_result_for_updated(self):
        archive_response_1 = \
            create_archive_response({'error_messages': ['Dummy error message']}, self.entity_type, is_update=True)
        archive_response_2 = \
            create_archive_response({'error_messages': ['Another dummy error message']}, self.entity_type, is_update=True)
        archive_response_3 = \
            create_archive_response({'error_messages': ['Yet another dummy error message']}, self.entity_type, is_update=True)

        archive_responses = [archive_response_1, archive_response_2, archive_response_3]
        processed_responses_from_archive =\
            self.biosamples_submitter.process_responses(self.submission, archive_responses, '', self.ARCHIVE_TYPE)

        assert_that(len(processed_responses_from_archive)).is_equal_to(1)
        assert_that(processed_responses_from_archive).contains('ERRORED')
        assert_that(processed_responses_from_archive.get('ERRORED')).is_equal_to(archive_responses)


if __name__ == '__main__':
    unittest.main()
