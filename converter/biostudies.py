from json_converter.json_mapper import JsonMapper

from converter.conversion_utils import fixed_attribute

PROJECT_SPEC_BASE = [
    {
        'name': ['', fixed_attribute, 'Project Core - Project Short Name'],
        'value': ['attributes.content.project_core.project_short_name']
    },
    {
        'name': ['', fixed_attribute, 'HCA Project UUID'],
        'value': ['attributes.uuid.uuid']
    },
    {
        'name': ['', fixed_attribute, 'ReleaseDate'],
        'value': ['attributes.releaseDate']
    },
    {
        'name': ['', fixed_attribute, 'AttachTo'],
        'value': ['', fixed_attribute, 'HCA']
    }
]

PROJECT_SPEC_SECTION = {
    "accno": ['', fixed_attribute, "PROJECT"],
    "type": ['', fixed_attribute, "Study"],
    "attributes": ['$array', [
            {
                "name": ['', fixed_attribute, "Title"],
                "value": ['attributes.content.project_core.project_title']
            },
            {
                "name": ['', fixed_attribute, "Description"],
                "value": ['attributes.content.project_core.project_description']
            }
        ],
        True
    ]
}


def array_to_string(*args):
    value = ", ".join(args[0])
    return value


PROJECT_SPEC_PUBLICATIONS = {
    "type": ['', fixed_attribute, "Publication"],
    "$on": 'publications',
    "attributes": ['$array', [
            {
                "name": ['', fixed_attribute, "Authors"],
                "value": ['authors', array_to_string]
            },
            {
                "name": ['', fixed_attribute, "Title"],
                "value": ['title']
            },
            {
                "name": ['', fixed_attribute, "doi"],
                "value": ['doi']
            },
            {
                "name": ['', fixed_attribute, "URL"],
                "value": ['url']
            }
        ],
        True
    ]
}


def _parse_name(*args):
    full_name = args[0]
    position = args[1]

    if not full_name:
        return None

    name_element = full_name.split(',', 2)[position]
    return name_element[0] if name_element and position == 1 else name_element


PROJECT_SPEC_AUTHORS = {
    "type": ['', fixed_attribute, "Author"],
    "$on": 'contributors',
    # '$filter': ['project_role', _is_not_wrangler],
    "attributes": ['$array', [
            {
                "name": ['', fixed_attribute, "First Name"],
                "value": ['name', _parse_name, 0]
            },
            {
                "name": ['', fixed_attribute, "Middle Initials"],
                "value": ['name', _parse_name, 1]
            },
            {
                "name": ['', fixed_attribute, "Last Name"],
                "value": ['name', _parse_name, 2]
            },
            {
                "name": ['', fixed_attribute, "Email"],
                "value": ['email']
            },
            {
                "name": ['', fixed_attribute, "Phone"],
                "value": ['phone']
            },
            {
                "name": ['', fixed_attribute, "Affiliation"],
                "value": ['institution']
            },
            {
                "name": ['', fixed_attribute, "Address"],
                "value": ['address']
            },
            {
                "name": ['', fixed_attribute, "Orcid ID"],
                "value": ['orcid_id']
            },
    ],
        True
    ]
}

PROJECT_SPEC_ORGANIZATIONS = {
    "type": ['', fixed_attribute, "Organization"],
    "$on": 'funders',
    "attributes": ['$array', [
            {
                "name": ['', fixed_attribute, "Grant ID"],
                "value": ['grant_id']
            },
            {
                "name": ['', fixed_attribute, "Grant Title"],
                "value": ['grant_title']
            },
            {
                "name": ['', fixed_attribute, "Organization"],
                "value": ['organization']
            },
    ],
        True
    ]
}


class BioStudiesConverter:

    def __init__(self):
        self.attributes = None
        self.contributors = None
        self.funders = None
        self.publications = None

    def convert(self, hca_project: dict) -> dict:
        converted_project = JsonMapper(hca_project).map({
            'attributes': ['$array', PROJECT_SPEC_BASE, True],
            'section': PROJECT_SPEC_SECTION
            })

        attributes = hca_project['attributes']
        project_content = attributes['content'] if 'content' in attributes else None
        if project_content:
            self.__add_subsections_to_project(converted_project, project_content)

        return converted_project

    @staticmethod
    def __add_subsections_to_project(converted_project, project_content):
        contributors = project_content['contributors']
        funders = project_content['funders']
        publications = project_content['publications']
        if contributors or funders or publications:
            converted_project['section']['subsections'] = []
        converted_publications = JsonMapper(project_content).map(PROJECT_SPEC_PUBLICATIONS)
        converted_authors = JsonMapper(project_content).map(PROJECT_SPEC_AUTHORS)
        converted_funders = JsonMapper(project_content).map(PROJECT_SPEC_ORGANIZATIONS)
        converted_project['section']['subsections'] = \
            converted_publications + converted_authors + converted_funders
