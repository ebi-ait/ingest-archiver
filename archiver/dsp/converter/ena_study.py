from conversion.post_process import prefix_with, default_to, format_date
from .abstracts import BaseDspConverter


class EnaStudyConverter(BaseDspConverter):
    prefix = 'study_'

    def convert(self, hca_data):
        core = 'content.project_core'
        spec = {
            '$on': 'project',
            'alias': ['uuid.uuid', prefix_with, self.prefix],
            'attributes': {
                'HCA Project UUID': ['uuid.uuid', self.dsp_attribute],
                'Project Core - Project Short Name': [f'{core}.project_short_name', self.dsp_attribute],
                'study_type': ['', self.fixed_dsp_attribute, 'Transcriptome Analysis'],
                'study_abstract': [f'{core}.project_description', self.dsp_attribute],
            },
            'title': [f'{core}.project_title'],
            'description': [f'{core}.project_description'],
            'releaseDate': ['releaseDate', format_date],
            'projectRef': {
                'alias': ['', default_to, '{projectAlias.placeholder}']
            }
        }
        if not hca_data.get('project', {}).get('releaseDate', None):
            spec['releaseDate'] = ['submissionDate', format_date]
        return self.map(hca_data, spec)
