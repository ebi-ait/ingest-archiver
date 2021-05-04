from converter.biosamples import BioSamplesConverter
from submission_broker.submission.submission import Submission, Entity
from submission_broker.services.biosamples import BioSamples, AapClient


class BioSamplesSubmitter:
    def __init__(self, biosamples: BioSamples, converter: BioSamplesConverter):
        self.__biosamples = biosamples
        self.__converter = converter

    def send_all_samples(self, submission: Submission) -> dict:
        response = {}
        project_release_date = self.__get_project_release_date_from_submission(submission)
        for sample in submission.get_entities('biomaterials'):
            result = self.send_sample(sample, project_release_date)
            response.setdefault(result, []).append(sample)
        return response

    def send_sample(self, sample: Entity, release_date: str = None) -> str:
        accession = sample.get_accession('BioSamples')
        biosample = self.__converter.convert(sample.attributes, release_date, accession)
        try:
            response = self.__biosamples.send_sample(biosample)
            if 'accession' in response and not accession:
                sample.add_accession('BioSamples', response['accession'])
                return f"CREATED"
            return f"UPDATED"
        except Exception as e:
            error_msg = f'BioSamples Error: {e}'
            sample.add_error('content.biomaterial_core.biosamples_accession', error_msg)
            return "ERRORED"

    @staticmethod
    def __get_project_release_date_from_submission(submission: Submission) -> str:
        projects = submission.get_entities('projects')
        for project in projects:
            if 'releaseDate' in project.attributes:
                return project.attributes['releaseDate']
