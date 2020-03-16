from archiver.dsp_post_process import dsp_attribute, fixed_dsp_attribute
from conversion.json_mapper import JsonMapper
from conversion.post_process import *

PREFIX_PROJECT = 'project_'
PREFIX_STUDY = 'study_'


def _parse_name(*args):
    full_name = args[0]
    position = args[1]
    name_element = full_name.split(',', 2)[position]
    return name_element[0] if name_element and position == 1 else name_element


def _is_not_wrangler(*args):
    project_role = args[0]
    text = project_role.get('text')
    is_wrangler = text is not None and 'wrangler' in text.lower()
    return not is_wrangler


project_spec = {
    '$on': 'project',
    'alias': ['uuid.uuid', prefix_with, PREFIX_PROJECT],
    'attributes': {
        'Project Core - Project Short Name': ['content.project_core.project_short_name', dsp_attribute],
        'HCA Project UUID': ['uuid.uuid', dsp_attribute]
    },
    'releaseDate': ['submissionDate', format_date],
    # TODO title probably needs padding? (len < 25)
    'title': ['content.project_core.project_title'],
    'description': ['content.project_core.project_description'],
    'contacts': {
        '$on': 'content.contributors',
        '$filter': ['project_role', _is_not_wrangler],
        'firstName': ['name', _parse_name, 0],
        'middleInitials': ['name', _parse_name, 1],
        'lastName': ['name', _parse_name, 2],
        'email': ['email', default_to, ''],
        'affiliation': ['institution', default_to, ''],
        'phone': ['phone', default_to, ''],
        'address': ['address', default_to, ''],
        'orcid': ['orcid', default_to, '']
    },
    'publications': {
        '$on': 'content.publications',
        'authors': ['authors', concatenate_list],
        'doi': ['doi', default_to, ''],
        'articleTitle': ['title', default_to, ''],
        'pubmedId': ['pmid', default_to, '']
    },
    'funders': {
        '$on': 'content.funders',
        'grantId': ['grant_id', default_to, ''],
        'grantTitle': ['grant_title', default_to, ''],
        'organization': ['organization', default_to, '']
    }
}


def convert_project(hca_data: dict):
    return JsonMapper(hca_data).map(project_spec)


study_spec = {
    '$on': 'project',
    'alias': ['uuid.uuid', prefix_with, (PREFIX_STUDY)],
    'attributes': {
        'HCA Project UUID': ['uuid.uuid', dsp_attribute],
        'Project Core - Project Short Name': ['content.project_core.project_short_name', dsp_attribute],
        'study_type': ['', fixed_dsp_attribute, 'Transcriptome Analysis'],
        'study_abstract': ['content.project_core.project_description', dsp_attribute],
    },
    'title': ['content.project_core.project_title'],
    'description': ['content.project_core.project_description'],
    'projectRef': {
        'alias': ['', default_to, '{projectAlias.placeholder}']
    }
}


def convert_study(hca_data: dict):
    return JsonMapper(hca_data).map(study_spec)
