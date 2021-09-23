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
        attributes = hca_project['attributes']
        contributors = hca_project['attributes']['content']['contributors']
        funders = hca_project['attributes']['content']['funders']
        publications = hca_project['attributes']['content']['publications']
        expected_payload = {
            "attributes": [
                {
                    "name": "Project Core - Project Short Name",
                    "value": attributes['content']['project_core']['project_short_name']
                },
                {
                    "name": "HCA Project UUID",
                    "value": attributes['uuid']['uuid']
                },
                {
                    "name": "ReleaseDate",
                    "value": attributes['releaseDate']
                }
            ],
            "section": {
                "accno": "PROJECT",
                "type": "Study",
                "attributes": [
                    {
                        "name": "Title",
                        "value": attributes['content']['project_core']['project_title']
                    },
                    {
                        "name": "Description",
                        "value": attributes['content']['project_core']['project_description']
                    }
                ],
                "subsections": [
                    {
                        "type": "Publication",
                        "attributes": [
                            {
                                "name": "Authors",
                                "value": ", ".join(publications[0]['authors'])
                            },
                            {
                                "name": "Title",
                                "value": publications[0]['title']
                            },
                            {
                                "name": "doi",
                                "value": publications[0]['doi']
                            },
                            {
                                "name": "URL",
                                "value": publications[0]['url']
                            }
                        ]
                    },
                    {
                        "type": "Author",
                        "attributes": [
                            {
                                "name": "First Name",
                                "value": _parse_name(contributors[0]['name'], 0)
                            },
                            {
                                "name": "Middle Initials",
                                "value": _parse_name(contributors[0]['name'], 1)
                            },
                            {
                                "name": "Last Name",
                                "value": _parse_name(contributors[0]['name'], 2)
                            },
                            {
                                "name": "Email",
                                "value": contributors[0]['email']
                            },
                            {
                                "name": "Phone",
                                "value": contributors[0]['phone']
                            },
                            {
                                "name": "Affiliation",
                                "value": contributors[0]['institution']
                            },
                            {
                                "name": "Address",
                                "value": contributors[0]['address']
                            },
                            {
                                "name": "Orcid ID",
                                "value": contributors[0]['orcid_id']
                            }
                        ]
                    },
                    {
                        "type": "Author",
                        "attributes": [
                            {
                                "name": "First Name",
                                "value": _parse_name(contributors[1]['name'], 0)
                            },
                            {
                                "name": "Middle Initials",
                                "value": _parse_name(contributors[1]['name'], 1)
                            },
                            {
                                "name": "Last Name",
                                "value": _parse_name(contributors[1]['name'], 2)
                            },
                            {
                                "name": "Email",
                                "value": contributors[1]['email']
                            },
                            {
                                "name": "Phone",
                                "value": contributors[1]['phone']
                            },
                            {
                                "name": "Affiliation",
                                "value": contributors[1]['institution']
                            },
                            {
                                "name": "Address",
                                "value": contributors[1]['address']
                            },
                            {
                                "name": "Orcid ID",
                                "value": contributors[1]['orcid_id']
                            }
                        ]
                    },
                    {
                        "type": "Organization",
                        "attributes": [
                            {
                                "name": "Grant ID",
                                "value": funders[0]['grant_id']
                            },
                            {
                                "name": "Grant Title",
                                "value": funders[0]['grant_title']
                            },
                            {
                                "name": "Organization",
                                "value": funders[0]['organization']
                            }
                        ]
                    },
                    {
                        "type": "Organization",
                        "attributes": [
                            {
                                "name": "Grant ID",
                                "value": funders[1]['grant_id']
                            },
                            {
                                "name": "Grant Title",
                                "value": funders[1]['grant_title']
                            },
                            {
                                "name": "Organization",
                                "value": funders[1]['organization']
                            }
                        ]
                    }
                ]
            }
        }

        return expected_payload


if __name__ == '__main__':
    unittest.main()
