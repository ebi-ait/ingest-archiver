import json
import unittest
from os.path import dirname

from assertpy import assert_that

from converter.ena.ena_study import EnaStudyConverter


class EnaStudyConverterTest(unittest.TestCase):

    def setUp(self) -> None:
        with open(dirname(__file__) + '/../../../resources/project.json') as file:
            self.project = json.load(file)

        self.ena_study_converter = EnaStudyConverter()

    def test_given_valid_ingest_project_accession_can_convert_to_ena_study(self):
        other_attributes = {
            'accession': 'SRP000123'
        }
        expected_payload = \
            self.__get_expected_payload('/../../../resources/expected_ena_study_payload_with_accession_and_alias.xml')

        converted_payload = self.ena_study_converter.convert(self.project['attributes'], other_attributes)

        assert_that(converted_payload).is_equal_to(expected_payload)

    def test_given_valid_ingest_project_without_accession_can_convert_to_ena_study(self):
        other_attributes = {
        }
        expected_payload = \
            self.__get_expected_payload('/../../../resources/expected_ena_study_payload_with_only_alias.xml')

        converted_payload = self.ena_study_converter.convert(self.project['attributes'], other_attributes)

        assert_that(converted_payload).is_equal_to(expected_payload)

    @staticmethod
    def __get_expected_payload(filename: str):
        with open(dirname(__file__) + filename) as file:
            return file.read()


if __name__ == '__main__':
    unittest.main()
