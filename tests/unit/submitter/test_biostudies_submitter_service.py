import json
import unittest
from os.path import dirname
from unittest.mock import MagicMock, Mock

from assertpy import assert_that

from submitter.biostudies_submitter_service import BioStudiesSubmitterService


class BioStudiesSubmitterServiceTest(unittest.TestCase):

    def setUp(self) -> None:
        self.archive_client = MagicMock()
        self.submitter_service = BioStudiesSubmitterService(self.archive_client)

    def test_when_pass_biosamples_accessions_then_submission_updated_with_their_links(self):
        self.maxDiff = None

        biosample_accessions = ["SAME_111", "SAME_222", "SAME_3333"]
        biostudies_submission = self.__get_original_payload()
        expected_biostudies_payload = self.__get_expected_payload()

        self.submitter_service.update_submission_with_accessions_by_type(
            biostudies_submission, biosample_accessions, BioStudiesSubmitterService.BIOSAMPLE_LINK_TYPE)

        assert_that(expected_biostudies_payload).is_equal_to(biostudies_submission)

    @staticmethod
    def __get_original_payload():
        with open(dirname(__file__) + '/../../resources/expected_biostudies_payload.json') as file:
            original_payload = json.load(file)

        return original_payload

    @staticmethod
    def __get_expected_payload():
        with open(dirname(__file__) + '/../../resources/expected_biostudies_payload_with_links.json') as file:
            expected_payload = json.load(file)
        return expected_payload


if __name__ == '__main__':
    unittest.main()
