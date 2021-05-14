from submission_broker.services.biostudies import BioStudies
from submission_broker.submission.submission import Submission, Entity

from converter.biostudies import BioStudiesConverter


class BioStudiesSubmitter:
    def __init__(self, biostudies_client: BioStudies, converter: BioStudiesConverter):
        self.__biostudies_client = biostudies_client
        self.__converter = converter

    def send_all_projects(self, submission: Submission) -> dict:
        response = {}
        for project in submission.get_entities('projects'):
            result = self.send_project(project)
            response.setdefault(result, []).append(project)
        return response

    def send_project(self, project: Entity) -> str:
        accession = project.get_accession('BioStudies')
        biostudy = self.__converter.convert(project.attributes)
        try:
            response = self.__biostudies_client.send_submission(biostudy)
            if 'accession' in response and not accession:
                project.add_accession('BioStudies', response['accession'])
                return 'CREATED'
            return 'UPDATED'
        except Exception as e:
            error_msg = f'BioStudies Error: {e}'
            project.add_error('content.project_core.biostudies_accession', error_msg)
            return 'ERRORED'
