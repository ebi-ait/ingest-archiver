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

    def test_given_valid_ingest_project_can_convert_to_ena_study(self):
        expected_payload = self.__get_expected_payload()

        converted_payload = self.ena_study_converter.convert(self.project['attributes'])

        assert_that(converted_payload).is_equal_to(expected_payload)

    @staticmethod
    def __get_expected_payload():
        with open(dirname(__file__) + '/../../../resources/expected_ena_study_payload.xml') as file:
            return file.read()


if __name__ == '__main__':
    unittest.main()
