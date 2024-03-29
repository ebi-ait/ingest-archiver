import unittest

from assertpy import assert_that
from biosamples_v4.models import Sample
from mock.mock import MagicMock, Mock
from requests import HTTPError

from archiver import ConvertedEntity
from hca.submission import HcaSubmission
from submitter.biosamples import BioSamplesSubmitter
from tests.unit.utils import make_ingest_entity, random_id, random_uuid


class TestBioSamplesSubmitter(unittest.TestCase):

    def setUp(self) -> None:
        self.client = MagicMock()
        self.converter = MagicMock()
        self.empty_sample1 = Sample(ncbi_taxon_id=9606)
        self.empty_sample2 = Sample(ncbi_taxon_id=9606)
        self.sample1 = Sample(ncbi_taxon_id=9606, name='test1')
        self.sample2 = Sample(ncbi_taxon_id=9606, name='test2')
        self.converter.convert = MagicMock(return_value=self.empty_sample1)
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
        is_create = not converted_entity.updated

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
        is_update = converted_entity.updated

        assert_that(converted_entity.data.accession).is_equal_to(accession)
        assert_that(is_update).is_true()

    def test_when_send_entities_to_archive_get_back_correct_archive_response(self):
        is_update = False
        converted_samples = [
            ConvertedEntity(data=self.empty_sample1, hca_entity_type=self.entity_type, is_update=is_update),
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
            assert_that(archive_response.get('entity_type')).is_equal_to(self.entity_type)
            assert_that(archive_response.get('is_update')).is_equal_to(is_update)

    def test_when_send_entities_without_name_to_archive_get_back_error_in_archive_response(self):
        is_update = False
        error_message1 = 'Sample name must be provided'
        error_message2 = 'Another error message'
        converted_samples = [
            ConvertedEntity(data=self.empty_sample1, hca_entity_type=self.entity_type, is_update=is_update),
            ConvertedEntity(data=self.empty_sample2, hca_entity_type=self.entity_type, is_update=is_update)
        ]
        self.client.send_sample = MagicMock(side_effect=[
                HTTPError(response=Mock(status=400, text=error_message1)),
                HTTPError(response=Mock(status=400, text=error_message2)),
            ]
        )
        archive_responses = self.biosamples_submitter.send_all_entities(converted_samples, self.ARCHIVE_TYPE)

        assert_that(len(archive_responses)).is_equal_to(len(converted_samples))
        for archive_response in archive_responses:
            assert_that(archive_response.get('entity_type')).is_equal_to(self.entity_type)
            assert_that(archive_response.get('is_update')).is_equal_to(is_update)
            assert_that(archive_response.get('error')).is_not_none()
            assert_that([error_message1, error_message2]).contains(archive_response.get('error'))


if __name__ == '__main__':
    unittest.main()
