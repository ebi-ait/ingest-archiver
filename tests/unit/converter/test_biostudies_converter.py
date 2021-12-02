import json
import unittest
from os.path import dirname

from assertpy import assert_that

from converter.biostudies import BioStudiesConverter


class TestBioStudiesConverter(unittest.TestCase):

    def setUp(self) -> None:
        with open(dirname(__file__) + '/../../resources/project.json') as file:
            self.project = json.load(file)

        self.biostudies_converter = BioStudiesConverter()

    def test_given_ingest_project_converts_correct_biostudies_payload(self):
        self.maxDiff = None
        expected_payload = self.__get_expected_payload('/../../resources/expected_biostudies_payload.json')

        converted_payload = self.biostudies_converter.convert(self.project['attributes'])

        self.assertEqual(json.dumps(expected_payload, sort_keys=True, indent=2),
                         json.dumps(converted_payload, sort_keys=True, indent=2))

    def test_given_ingest_project_converts_project_twice_should_return_correct_biostudies_payload(self):
        self.maxDiff = None
        expected_payload = self.__get_expected_payload('/../../resources/expected_biostudies_payload.json')
        biostudies_converter2 = BioStudiesConverter()

        self.biostudies_converter.convert(self.project['attributes'])
        converted_payload = biostudies_converter2.convert(self.project['attributes'])

        self.assertEqual(json.dumps(expected_payload, sort_keys=True, indent=2),
                         json.dumps(converted_payload, sort_keys=True, indent=2))

    def test_convert_full_name_with_middle_initials_returns_3_name_parts(self):
        full_name = "Joe,Doe,Smith"

        name_parts: dict = self.biostudies_converter.convert_full_name(full_name)

        assert_that(name_parts.get('first_name')).is_equal_to("Joe")
        assert_that(name_parts.get('middle_initials')).is_equal_to("D")
        assert_that(name_parts.get('last_name')).is_equal_to("Smith")

    def test_convert_full_name_without_middle_initials_returns_2_name_parts(self):
        full_name = "Joe,,Smith"

        name_parts: dict = self.biostudies_converter.convert_full_name(full_name)

        assert_that(name_parts.get('first_name')).is_equal_to("Joe")
        assert_that(name_parts.get('middle_initials')).is_none()
        assert_that(name_parts.get('last_name')).is_equal_to("Smith")

    def test_convert_full_name_with_only_2_parts_returns_2_name_parts(self):
        full_name = "Joe,Smith"

        name_parts: dict = self.biostudies_converter.convert_full_name(full_name)

        assert_that(name_parts.get('first_name')).is_equal_to("Joe")
        assert_that(name_parts.get('middle_initials')).is_none()
        assert_that(name_parts.get('last_name')).is_equal_to("Smith")

    def test_when_no_entry_attributes_then_all_of_them_added_as_attributes(self):
        specification = {
            'type': 'Author',
            'on': 'contributors',
            'attributes_to_include': {
                'first_name': 'First Name',
                'middle_initials': 'Middle Initials',
                'last_name': 'Last Name'
            }
        }
        project_content = {
            "contributors": [
                {
                    "first_name": "Joe",
                    "middle_initials": "Doe",
                    "last_name": "Smith"
                }
            ]
        }

        subsection_payload_elements = self.biostudies_converter.add_attributes_by_spec(
            specification, project_content)

        assert_that(subsection_payload_elements).is_length(1)
        subsection_payload_element = subsection_payload_elements[0]
        assert_that(subsection_payload_element).contains("attributes")
        assert_that(subsection_payload_element.get("attributes")).is_length(3)
        assert_that(subsection_payload_element.get("attributes")[1]).is_length(2)
        assert_that(subsection_payload_element.get("attributes")).contains(
            {
                "name": "Middle Initials",
                "value": "Doe"
            }
        )

    def test_when_attribute_empty_then_wont_be_added_as_an_attribute(self):
        specification = {
            'type': 'Author',
            'on': 'contributors',
            'attributes_to_include': {
                'first_name': 'First Name',
                'middle_initials': 'Middle Initials',
                'last_name': 'Last Name'
            }
        }
        project_content = {
            "contributors": [
                {
                    "first_name": "Joe",
                    "middle_initials": "",
                    "last_name": "Smith"
                }
            ]
        }

        subsection_payload_elements = self.biostudies_converter.add_attributes_by_spec(
            specification, project_content)

        assert_that(subsection_payload_elements).is_length(1)
        subsection_payload_element = subsection_payload_elements[0]

        assert_that(subsection_payload_element).contains("attributes")
        assert_that(subsection_payload_element.get("attributes")).is_length(2)
        assert_that(subsection_payload_element.get("attributes")[1]).is_length(2)
        assert_that(subsection_payload_element.get("attributes")).does_not_contain(
            {
                "name": "Middle Initials",
                "value": ""
            }
        )

    def test_given_ingest_project_with_empty_values_converts_correct_biostudies_payload(self):
        self.maxDiff = None
        expected_payload = self.__get_expected_payload('/../../resources/expected_biostudies_payload_without_empty_values.json')

        converted_payload = self.biostudies_converter.convert(self.project['attributes'])

        self.assertEqual(json.dumps(expected_payload, sort_keys=True, indent=2),
                         json.dumps(converted_payload, sort_keys=True, indent=2))

    @staticmethod
    def __get_expected_payload(file_path: str):
        with open(dirname(__file__) + file_path) as file:
            expected_payload = json.load(file)
        return expected_payload


if __name__ == '__main__':
    unittest.main()
