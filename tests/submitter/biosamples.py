import datetime
import unittest

from biosamples_v4.models import Sample
from mock import MagicMock

from hca.submission import HcaSubmission
from submitter.biosamples import BioSamplesSubmitter
from tests.utils import make_ingest_entity, random_id, random_uuid


class TestBioSamplesSubmitter(unittest.TestCase):
    def setUp(self) -> None:
        self.biosamples = MagicMock()
        self.biosamples.send_sample = MagicMock()
        self.converter = MagicMock()
        self.empty_sample = Sample(ncbi_taxon_id=9606)
        self.converter.convert = MagicMock(return_value=self.empty_sample)
        self.submitter = BioSamplesSubmitter(self.biosamples, self.converter)
        self.submission = HcaSubmission()

    def test_submit_sample_converts_and_sends_sample(self):
        # Given
        test_case = self.submission.map_ingest_entity(
            make_ingest_entity('biomaterials', random_id(), random_uuid())
        )
        # When
        result = self.submitter.send_sample(test_case)

        # Then
        self.converter.convert.assert_called_once_with(test_case.attributes, release_date=None, accession=None)
        self.biosamples.send_sample.assert_called_once_with(self.empty_sample)
        self.assertEqual('UPDATED', result)

    def test_submit_sample_with_date_converts_and_sends_sample(self):
        # Given
        test_case = self.submission.map_ingest_entity(
            make_ingest_entity('biomaterials', random_id(), random_uuid())
        )
        test_date = datetime.datetime.now().isoformat()
        # When
        result = self.submitter.send_sample(test_case, test_date)

        # Then
        self.converter.convert.assert_called_once_with(test_case.attributes, release_date=test_date, accession=None)
        self.biosamples.send_sample.assert_called_once_with(self.empty_sample)
        self.assertEqual('UPDATED', result)

    def test_submit_sample_with_accession_converts_and_sends_sample(self):
        # Given
        test_case = self.submission.map_ingest_entity(
            make_ingest_entity('biomaterials', random_id(), random_uuid())
        )
        test_case.add_accession('BioSamples', 'SAMEA1234567')
        # When
        result = self.submitter.send_sample(test_case)

        # Then
        self.converter.convert.assert_called_once_with(test_case.attributes, release_date=None, accession='SAMEA1234567')
        self.biosamples.send_sample.assert_called_once_with(self.empty_sample)
        self.assertEqual('UPDATED', result)

    def test_submit_sample_return_creation(self):
        # Given
        self.biosamples.send_sample = MagicMock(return_value={'accession': 'SAMEA1234567'})
        test_case = self.submission.map_ingest_entity(make_ingest_entity('biomaterials', random_id(), random_uuid()))
        # When
        result = self.submitter.send_sample(test_case)
        # Then
        self.assertEqual('CREATED', result)

    def test_submit_sample_return_error(self):
        # Given
        error_msg = f'TestCaseError{random_id(3)}'
        self.biosamples.send_sample = MagicMock(side_effect=Exception(error_msg))
        test_case = self.submission.map_ingest_entity(
            make_ingest_entity('biomaterials', random_id(), random_uuid()))
        # When
        result = self.submitter.send_sample(test_case)
        # Then
        self.assertEqual('ERRORED', result)
        self.assertDictEqual(test_case.get_errors(), {'content.biomaterial_core.biosamples_accession': [f'BioSamples Error: {error_msg}']})


if __name__ == '__main__':
    unittest.main()
