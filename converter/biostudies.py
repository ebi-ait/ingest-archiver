import json
import logging

from json_converter.json_mapper import JsonMapper
from json_converter.post_process import default_to

ACCNO_PREFIX_FOR_ORGANIZATIONS = "o"

ACCNO_PREFIX_FOR_AUTHORS = "a"


def array_to_string(*args):
    value = ", ".join(args[0])
    return value

def _parse_name(*args):
    full_name = args[0]
    position = args[1]

    if not full_name:
        return None

    name_element = full_name.split(',', 2)[position]
    return name_element[0] if name_element and position == 1 else name_element


class BioStudiesConverter:

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.attributes = None
        self.contributors = None
        self.funders = None
        self.publications = None
        self.project_spec_base = [
            {
                'name': ['', default_to, 'Project Core - Project Short Name'],
                'value': ['content.project_core.project_short_name']
            },
            {
                'name': ['', default_to, 'HCA Project UUID'],
                'value': ['uuid.uuid']
            },
            {
                'name': ['', default_to, 'ReleaseDate'],
                'value': ['releaseDate']
            }
        ]
        self.project_spec_section = {
            "accno": ['', default_to, "PROJECT"],
            "type": ['', default_to, "Study"],
            "attributes": ['$array', [
                    {
                        "name": ['', default_to, "Title"],
                        "value": ['content.project_core.project_title']
                    },
                    {
                        "name": ['', default_to, "Description"],
                        "value": ['content.project_core.project_description']
                    }
                ],
                True
            ]
        }
        self.project_spec_publications = {
            "type": ['', default_to, "Publication"],
            "$on": 'publications',
            "attributes": ['$array', [
                {
                    "name": ['', default_to, "Authors"],
                    "value": ['authors', array_to_string]
                },
                {
                    "name": ['', default_to, "Title"],
                    "value": ['title']
                },
                {
                    "name": ['', default_to, "doi"],
                    "value": ['doi']
                },
                {
                    "name": ['', default_to, "URL"],
                    "value": ['url']
                }
            ],
                           True
                           ]
        }
        self.project_spec_authors = {
            "type": ['', default_to, "Author"],
            "$on": 'contributors',
            "attributes": ['$array', [
                    {
                        "name": ['', default_to, "Name"],
                        "value": ['name']
                    },
                    {
                        "name": ['', default_to, "First Name"],
                        "value": ['name', _parse_name, 0]
                    },
                    {
                        "name": ['', default_to, "Middle Initials"],
                        "value": ['name', _parse_name, 1]
                    },
                    {
                        "name": ['', default_to, "Last Name"],
                        "value": ['name', _parse_name, 2]
                    },
                    {
                        "name": ['', default_to, "Email"],
                        "value": ['email']
                    },
                    {
                        "name": ['', default_to, "Phone"],
                        "value": ['phone']
                    },
                    {
                        "name": ['', default_to, "Address"],
                        "value": ['address']
                    },
                    {
                        "name": ['', default_to, "Orcid ID"],
                        "value": ['orcid_id']
                    },
            ],
                True
            ]
        }
        self.project_spec_fundings = {
            "type": ['', default_to, "Funding"],
            "$on": 'funders',
            "attributes": ['$array', [
                    {
                        "name": ['', default_to, "grant_id"],
                        "value": ['grant_id']
                    },
                    {
                        "name": ['', default_to, "Grant Title"],
                        "value": ['grant_title']
                    },
                    {
                        "name": ['', default_to, "Agency"],
                        "value": ['organization']
                    },
            ],
                True
            ]
        }

    def convert(self, hca_project: dict, additional_attributes: dict = None) -> dict:
        if hca_project:
            self.logger.info(f'hca_project: {json.dumps(hca_project)}')
            self.logger.info(f'PROJECT_SPEC_BASE: {self.project_spec_base}')
            self.logger.info(f'PROJECT_SPEC_SECTION: {self.project_spec_section}')
        else:
            self.logger.info(f'hca_project is falsy')

        converted_project = JsonMapper(hca_project).map({
            'attributes': ['$array', self.project_spec_base, True],
            'section': self.project_spec_section
            })

        project_content = hca_project['content'] if 'content' in hca_project else None
        if project_content:
            self.__add_subsections_to_project(converted_project, project_content)

        return converted_project

    def __add_subsections_to_project(self, converted_project, project_content):
        contributors = project_content.get('contributors')
        funders = project_content.get('funders')
        publications = project_content.get('publications')
        if contributors or funders or publications:
            converted_project['section']['subsections'] = []

        converted_publications = JsonMapper(project_content).map(self.project_spec_publications) if publications else []

        converted_organizations = []

        converted_authors = JsonMapper(project_content).map(self.project_spec_authors) if contributors else []
        BioStudiesConverter.__add_accno(converted_authors, ACCNO_PREFIX_FOR_AUTHORS)
        BioStudiesConverter.__add_affiliation(contributors, converted_authors, converted_organizations)

        converted_funders = JsonMapper(project_content).map(self.project_spec_fundings) if funders else []

        converted_project['section']['subsections'] = \
            converted_publications + converted_authors + converted_organizations + converted_funders

    @staticmethod
    def __add_accno(converted_authors, prefix):
        for index, author in enumerate(converted_authors, start=1):
            author['accno'] = prefix + str(index)

    @staticmethod
    def __add_affiliation(contributors: list, converted_authors: list, converted_organizations: list):
        index = 1
        for contributor in contributors:
            affiliation = {}
            if 'institution' in contributor:
                author: dict = BioStudiesConverter.__get_author_by_name(contributor.get('name'), converted_authors)
                affiliation['name'] = 'affiliation'
                affiliation['reference'] = True
                affiliation['value'] = 'o' + str(index)
                author.get('attributes').append(affiliation)

                converted_organizations.append(
                    BioStudiesConverter.__add_new_organization(contributor.get('institution'), index))

                index += 1

    @staticmethod
    def __get_author_by_name(contributor_name: str, authors: list):
        for author in authors:
            for attribute in author.get('attributes'):
                if attribute.get('name') == 'Name' and attribute.get('value') == contributor_name:
                    return author
        return None

    @staticmethod
    def __add_new_organization(organization_name: str, index: int):
        return \
            {
                'accno': ACCNO_PREFIX_FOR_ORGANIZATIONS + str(index),
                'type': "Organization",
                'attributes': [
                    {
                        'name': 'Name',
                        'value': organization_name
                    }
                ]
            }
