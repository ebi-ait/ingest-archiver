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
        self.ena_study_converter.init_ena_set()

    def test_given_valid_ingest_project_accession_can_convert_to_ena_study(self):
        other_attributes = {
            'accession': 'SRP000123',
            'alias': 'fc55bd4a-8694-4a28-9a35-59a685bda323'
        }
        expected_payload = \
            self.__get_expected_payload('/../../../resources/expected_ena_study_payload_with_accession_and_alias.xml')

        self.ena_study_converter.convert(self.project['attributes'], other_attributes)

        converted_payload = self.ena_study_converter.convert_entity_to_xml_str().decode("UTF-8")

        assert_that(converted_payload).is_equal_to(expected_payload)

    def test_given_valid_ingest_project_without_accession_can_convert_to_ena_study(self):
        other_attributes = {
            'alias': 'fc55bd4a-8694-4a28-9a35-59a685bda323'
        }
        expected_payload = \
            self.__get_expected_payload('/../../../resources/expected_ena_study_payload_with_only_alias.xml')

        self.ena_study_converter.convert(self.project['attributes'], other_attributes)

        converted_payload = self.ena_study_converter.convert_entity_to_xml_str().decode("UTF-8")

        assert_that(converted_payload).is_equal_to(expected_payload)

    @staticmethod
    def __get_expected_payload(filename: str):
        with open(dirname(__file__) + filename) as file:
            return file.read()


if __name__ == '__main__':
    unittest.main()
