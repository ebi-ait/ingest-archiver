import json
import unittest
from os.path import dirname

from assertpy import assert_that

from converter.ena.ena_sample import EnaSampleConverter
from converter.ena.ena_study import EnaStudyConverter


class EnaSampleConverterTest(unittest.TestCase):

    def setUp(self) -> None:
        with open(dirname(__file__) + '/../../../resources/biomaterial_entity.json') as file:
            self.biomaterial = json.load(file)

        self.ena_sample_converter = EnaSampleConverter()

    def test_given_valid_ingest_biomaterial_with_accession_can_convert_to_ena_sample(self):
        other_attributes = {
            'accession': 'ERS123456'
        }
        expected_payload = \
            self.__get_expected_payload('/../../../resources/expected_ena_sample_payload_with_accession_and_alias.xml')

        converted_payload = self.ena_sample_converter.convert(self.biomaterial['attributes'], other_attributes).decode("UTF-8")

        assert_that(converted_payload).is_equal_to(expected_payload)

    def test_given_valid_ingest_biomaterial_without_accession_can_convert_to_ena_sample(self):
        other_attributes = {
        }
        expected_payload = \
            self.__get_expected_payload('/../../../resources/expected_ena_sample_payload_with_only_alias.xml')

        converted_payload = self.ena_sample_converter.convert(self.biomaterial['attributes'], other_attributes).decode("UTF-8")

        assert_that(converted_payload).is_equal_to(expected_payload)

    @staticmethod
    def __get_expected_payload(filename: str):
        with open(dirname(__file__) + filename) as file:
            return file.read()


if __name__ == '__main__':
    unittest.main()
