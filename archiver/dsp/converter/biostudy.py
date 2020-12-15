from conversion.post_process import prefix_with, default_to, format_date, concatenate_list
from .abstracts import BaseDspConverter


class BiostudyConverter(BaseDspConverter):
    prefix = 'project_'

    def convert(self, hca_data: dict):
        core = 'content.project_core'
        spec = {
            '$on': 'project',
            'alias': ['uuid.uuid', prefix_with, self.prefix],
            'attributes': {
                'Project Core - Project Short Name': [f'{core}.project_short_name', self.dsp_attribute],
                'HCA Project UUID': ['uuid.uuid', self.dsp_attribute]
            },
            'releaseDate': ['releaseDate', format_date],
            # TODO title probably needs padding? (len < 25)
            'title': [f'{core}.project_title'],
            'description': [f'{core}.project_description'],
            'contacts': {
                '$on': 'content.contributors',
                '$filter': ['project_role', self.is_not_wrangler],
                'firstName': ['name', self.parse_name, 0],
                'middleInitials': ['name', self.parse_name, 1],
                'lastName': ['name', self.parse_name, 2],
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
        if not hca_data.get('project', {}).get('releaseDate', None):
            spec['releaseDate'] = ['submissionDate', format_date]
        return self.map(hca_data, spec)

    @staticmethod
    def is_not_wrangler(*args):
        project_role = args[0]
        text = project_role.get('text')
        return text is not None and 'wrangler' in text.lower()

    @staticmethod
    def parse_name(*args):
        full_name = args[0]
        position = args[1]

        if not full_name:
            return None

        name_element = full_name.split(',', 2)[position]
        return name_element[0] if name_element and position == 1 else name_element
