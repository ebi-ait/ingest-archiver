from hca.loader import HcaLoader
from .submission import DuplicateSubmission


class DuplicateLoader(HcaLoader):
    def duplicate_project(self, project_uuid: str, submission: DuplicateSubmission = None) -> DuplicateSubmission:
        if not submission:
            submission = DuplicateSubmission()
        self._map_project(submission, project_uuid)
        return submission

    def duplicate_submission(self, submission_uuid: str, submission: DuplicateSubmission = None) -> DuplicateSubmission:
        if not submission:
            submission = DuplicateSubmission()
        self._map_submission(submission, submission_uuid)
        return submission
