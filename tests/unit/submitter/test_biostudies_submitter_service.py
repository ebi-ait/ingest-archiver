import json
import unittest
from os.path import dirname
from unittest.mock import MagicMock, Mock

from submitter.biostudies_submitter_service import BioStudiesSubmitterService


class BioStudiesSubmitterServiceTest(unittest.TestCase):

    def setUp(self) -> None:
        self.archive_client = MagicMock()
        self.archive_client.get_submission_by_accession.return_value = \
            self.__get_original_payload()
        self.submitter_service = BioStudiesSubmitterService(self.archive_client)

    def test_when_biosamples_accession_is_empty_then_submission_not_changed(self):
        biosample_accessions = []
        biostudies_accession = "bst_123"
        expected_biostudies_payload = None

        biostudies_payload = \
            self.submitter_service.update_submission_with_sample_accessions(biosample_accessions, biostudies_accession)

        self.assertEqual(expected_biostudies_payload, biostudies_payload)

    def test_when_pass_biosamples_accessions_then_submission_updated_with_their_links(self):
        self.maxDiff = None

        biosample_accessions = ["SAME_111", "SAME_222", "SAME_3333"]
        biostudies_accession = "bst_123"
        expected_biostudies_payload = self.__get_expected_payload()

        biostudies_payload = \
            self.submitter_service.update_submission_with_sample_accessions(biosample_accessions, biostudies_accession)

        self.assertEqual(json.dumps(expected_biostudies_payload, sort_keys=True, indent=2),
                         json.dumps(biostudies_payload, sort_keys=True, indent=2))

    @staticmethod
    def __get_original_payload():
        with open(dirname(__file__) + '/../../resources/expected_biostudies_payload.json') as file:
            original_payload = json.load(file)

        mock_response = MagicMock()
        mock_response.json = original_payload

        return mock_response

    @staticmethod
    def __get_expected_payload():
        with open(dirname(__file__) + '/../../resources/expected_biostudies_payload_with_links.json') as file:
            expected_payload = json.load(file)
        return expected_payload


if __name__ == '__main__':
    unittest.main()
