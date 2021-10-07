import json
import unittest
from os.path import dirname

from converter.biostudies import BioStudiesConverter, _parse_name


class TestBioStudiesConverter(unittest.TestCase):

    def setUp(self) -> None:
        with open(dirname(__file__) + '/../../resources/projects.json') as file:
            self.projects = json.load(file)

        self.biostudies_converter = BioStudiesConverter()

    def test_given_ingest_project_converts_correct_biostudies_payload(self):
        self.maxDiff = None
        project = self.__get_project_by_index(0)
        expected_payload = self.__get_expected_payload(project)

        converted_payload = self.biostudies_converter.convert(project['attributes'])

        self.assertEqual(json.dumps(expected_payload, sort_keys=True, indent=2),
                         json.dumps(converted_payload, sort_keys=True, indent=2))

    def __get_project_by_index(self, index):
        return list(self.projects['projects'].values())[index]

    @staticmethod
    def __get_expected_payload(hca_project):
        with open(dirname(__file__) + '/../../resources/expected_biostudies_payload.json') as file:
            expected_payload = json.load(file)
        return expected_payload


if __name__ == '__main__':
    unittest.main()
