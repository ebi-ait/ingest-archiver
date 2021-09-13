import unittest
from datetime import datetime
from typing import List

from mock import MagicMock, call

from biosamples_v4.models import Sample
from hca.submission import HcaSubmission, Entity
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
        test_date = datetime.now().isoformat()
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

    def test_send_all_samples_sends_each_samples_with_project_release_date(self):
        # Given
        self.submitter.send_sample = MagicMock(return_value='UPDATED')
        test_date = datetime.now().isoformat()
        project_attributes = {
            'releaseDate': test_date
        }
        project_attributes = make_ingest_entity('projects', random_id(), random_uuid(), project_attributes)
        self.submission.map_ingest_entity(project_attributes)
        biomaterials = self.map_random_biomaterials(self.submission, 5)
        calls = []
        call_count = 0
        expected_result = {'UPDATED': []}
        for entity in biomaterials:
            call_count += 1
            calls.append(call(entity, test_date))
            expected_result['UPDATED'].append(entity)

        # When
        result = self.submitter.send_all_samples(self.submission)

        # Then
        self.submitter.send_sample.assert_has_calls(calls, any_order=True)
        self.assertEqual(call_count, self.submitter.send_sample.call_count)
        self.assertDictEqual(expected_result, result)

    def test_send_all_samples_sorts_samples_into_results(self):
        # Given
        self.submitter.send_sample = MagicMock(side_effect=['UPDATED', 'CREATED', 'ERRORED'])
        biomaterials = self.map_random_biomaterials(self.submission, 3)
        calls = []
        call_count = 0
        for entity in biomaterials:
            call_count += 1
            calls.append(call(entity, None))

        # When
        result = self.submitter.send_all_samples(self.submission)

        # Then
        self.submitter.send_sample.assert_has_calls(calls, any_order=True)
        self.assertEqual(call_count, self.submitter.send_sample.call_count)
        self.assertEqual(1, len(result['UPDATED']))
        self.assertEqual(1, len(result['CREATED']))
        self.assertEqual(1, len(result['ERRORED']))

    @staticmethod
    def map_random_biomaterials(submission: HcaSubmission, entity_count: int) -> List[Entity]:
        biomaterials = []
        for i in range(0, entity_count):
            biomaterials.append(
                submission.map_ingest_entity(
                    make_ingest_entity('biomaterials', random_id(), random_uuid())
                )
            )
        return biomaterials


if __name__ == '__main__':
    unittest.main()
