from json_converter.json_mapper import JsonMapper
from json_converter.post_process import default_to

PROJECT_SPEC_BASE = [
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

PROJECT_SPEC_SECTION = {
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


def array_to_string(*args):
    value = ", ".join(args[0])
    return value


PROJECT_SPEC_PUBLICATIONS = {
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


def _parse_name(*args):
    full_name = args[0]
    position = args[1]

    if not full_name:
        return None

    name_element = full_name.split(',', 2)[position]
    return name_element[0] if name_element and position == 1 else name_element


PROJECT_SPEC_AUTHORS = {
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
                "name": ['', default_to, "affiliation"],
                "value": ['institution']
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

PROJECT_SPEC_FUNDINGS = {
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


class BioStudiesConverter:

    def __init__(self):
        self.attributes = None
        self.contributors = None
        self.funders = None
        self.publications = None

    def convert(self, hca_project: dict, additional_attributes: dict = None) -> dict:
        converted_project = JsonMapper(hca_project).map({
            'attributes': ['$array', PROJECT_SPEC_BASE, True],
            'section': PROJECT_SPEC_SECTION
            })

        project_content = hca_project['content'] if 'content' in hca_project else None
        if project_content:
            self.__add_subsections_to_project(converted_project, project_content)

        return converted_project

    @staticmethod
    def __add_subsections_to_project(converted_project, project_content):
        contributors = project_content.get('contributors')
        funders = project_content.get('funders')
        publications = project_content.get('publications')
        if contributors or funders or publications:
            converted_project['section']['subsections'] = []

        converted_publications = JsonMapper(project_content).map(PROJECT_SPEC_PUBLICATIONS) if publications else []
        converted_authors = JsonMapper(project_content).map(PROJECT_SPEC_AUTHORS) if contributors else []

        BioStudiesConverter.__add_accno_to_authors(converted_authors)

        converted_funders = JsonMapper(project_content).map(PROJECT_SPEC_FUNDINGS) if funders else []

        converted_project['section']['subsections'] = \
            converted_publications + converted_authors + converted_funders

    @staticmethod
    def __add_accno_to_authors(converted_authors):
        for index, author in enumerate(converted_authors, start=1):
            author['accno'] = 'a' + str(index)
