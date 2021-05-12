from hca.loader import HcaLoader
from .submission import DuplicateSubmission


class DuplicateLoader(HcaLoader):
    def duplicate_project(self, project_uuid: str) -> DuplicateSubmission:
        hca_submission = DuplicateSubmission()
        project_type = 'projects'
        project = self.__map_entity(hca_submission, project_type, project_uuid)
        submission_type = 'submissionEnvelopes'
        self.__map_link_type_to_link_names(hca_submission, project, submission_type)
        for submission_entity in hca_submission.get_entities(submission_type):
            self.__map_submission_manifests(hca_submission, submission_entity)
        return hca_submission

    def duplicate_submission(self, submission_uuid: str) -> DuplicateSubmission:
        hca_submission = DuplicateSubmission()
        submission_type = 'submissionEnvelopes'
        submission_entity = self.__map_entity(hca_submission, submission_type, submission_uuid)
        self.__map_submission_manifests(hca_submission, submission_entity)
        return hca_submission
