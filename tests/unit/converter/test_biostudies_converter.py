import json
import unittest
from os.path import dirname

from converter.biostudies import BioStudiesConverter


class TestBioStudiesConverter(unittest.TestCase):

    def setUp(self) -> None:
        with open(dirname(__file__) + '/../../resources/project.json') as file:
            self.project = json.load(file)

        self.biostudies_converter = BioStudiesConverter()

    def test_given_ingest_project_converts_correct_biostudies_payload(self):
        self.maxDiff = None
        expected_payload = self.__get_expected_payload()

        converted_payload = self.biostudies_converter.convert(self.project['attributes'])

        self.assertEqual(json.dumps(expected_payload, sort_keys=True, indent=2),
                         json.dumps(converted_payload, sort_keys=True, indent=2))

    @staticmethod
    def __get_expected_payload():
        with open(dirname(__file__) + '/../../resources/expected_biostudies_payload.json') as file:
            expected_payload = json.load(file)
        return expected_payload


if __name__ == '__main__':
    unittest.main()
