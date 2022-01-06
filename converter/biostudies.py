import copy
from datetime import datetime

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


PUBLICATION_SPEC = {
    'type': 'Publication',
    'on': 'publications',
    'attributes_to_include': {
        'authors': "Authors",
        'title': "Title",
        'doi': 'doi',
        'url': 'URL'
    },
    'attribute_handler': {
        'authors': array_to_string
    }
}
AUTHORS_SPEC = {
    'type': 'Author',
    'on': 'contributors',
    'attributes_to_include': {
        'name': 'Name',
        'first_name': 'First Name',
        'middle_initials': 'Middle Initials',
        'last_name': 'Last Name',
        'email': 'Email',
        'phone': 'Phone',
        'address': 'Address',
        'orcid_id': 'Orcid ID'
    }
}
FUNDING_SPEC = {
    'type': 'Funding',
    'on': 'funders',
    'attributes_to_include': {
        'grant_id': 'grant_id',
        'grant_title': 'Grant Title',
        'organization': 'Agency'
    }
}


class BioStudiesConverter:

    def __init__(self):
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
            'accno': ['', default_to, 'PROJECT'],
            'type': ['', default_to, 'Study'],
            'attributes': ['$array', [
                    {
                        'name': ['', default_to, 'Title'],
                        'value': ['content.project_core.project_title']
                    },
                    {
                        'name': ['', default_to, 'Description'],
                        'value': ['content.project_core.project_description']
                    }
                ],
                True
            ]
        }

    def convert(self, hca_project: dict, additional_attributes: dict = None) -> dict:
        if hca_project.get('releaseDate') is None:
            self.__set_release_date(hca_project)

        converted_project = JsonMapper(hca_project).map({
            'attributes': ['$array', self.project_spec_base, True],
            'section': self.project_spec_section
            })

        project_content = hca_project['content'] if 'content' in hca_project else None
        if project_content:
            self.__add_subsections_to_project(converted_project, project_content)

        return converted_project

    @staticmethod
    def __set_release_date(hca_project: dict):
        hca_project.update({'releaseDate': datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")})

    def __add_subsections_to_project(self, converted_project, project_content):
        contributors = project_content.get('contributors')
        funders = project_content.get('funders')
        publications = project_content.get('publications')
        if contributors or funders or publications:
            converted_project['section']['subsections'] = []

        converted_publications = self.add_attributes_by_spec(PUBLICATION_SPEC, project_content)

        converted_organizations = []

        project_content_with_structured_names = self.transform_author_names(project_content)
        converted_authors = self.add_attributes_by_spec(AUTHORS_SPEC, project_content_with_structured_names) if contributors else []
        BioStudiesConverter.__add_accno(converted_authors, ACCNO_PREFIX_FOR_AUTHORS)
        BioStudiesConverter.__add_affiliation(contributors, converted_authors, converted_organizations)

        converted_funders = self.add_attributes_by_spec(FUNDING_SPEC, project_content) if funders else []

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
                'type': 'Organization',
                'attributes': [
                    {
                        'name': 'Name',
                        'value': organization_name
                    }
                ]
            }

    @staticmethod
    def transform_author_names(project_content: dict) -> dict:
        project_content_with_structured_name = copy.deepcopy(project_content)
        contributors = project_content_with_structured_name.get('contributors')
        contributor: dict
        for contributor in contributors:
            full_name = contributor.get('name')
            structured_name = BioStudiesConverter.convert_full_name(full_name)
            contributor.update(structured_name)

        return project_content_with_structured_name

    @staticmethod
    def add_attributes_by_spec(specification: dict, project_content: dict):
        subsection_type_list = []
        iterate_on = specification.get('on')
        attributes_to_include: dict = specification.get('attributes_to_include')
        for entity in project_content.get(iterate_on):
            subsection_payload_element = {}
            attribute_list = []
            for attribute_key in attributes_to_include:
                if entity.get(attribute_key):
                    attribute_handler = specification.get('attribute_handler', {}).get(attribute_key)
                    value = entity.get(attribute_key)
                    if attribute_handler:
                        value = attribute_handler(value)
                    attribute_list.append(
                        {
                            'name': attributes_to_include.get(attribute_key),
                            'value': value
                        }
                    )
            if len(attribute_list) > 0:
                subsection_payload_element.update(
                    {
                        'type': specification.get('type'),
                        'attributes': attribute_list
                    }
                )
            subsection_type_list.append(subsection_payload_element)
        return subsection_type_list

    @staticmethod
    def convert_full_name(full_name: str) -> dict:
        if full_name is None:
            return {}
        name_parts = full_name.split(',', 2)

        first_name = name_parts[0]
        if len(name_parts) <= 2:
            middle_initials = None
            last_name = name_parts[1]
        else:
            middle_initials = name_parts[1][0] if name_parts[1] else None
            last_name = name_parts[2]

        structured_name = {
            'first_name': first_name,
            'last_name': last_name
        }

        if middle_initials:
            structured_name['middle_initials'] = middle_initials

        return structured_name
