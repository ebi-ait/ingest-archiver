import logging
import polling as polling

from archiver.usiapi import USIAPI
from archiver.converter import Converter, ConversionError

VALIDATION_POLLING_TIMEOUT = 10
VALIDATION_POLLING_STEP = 2

SUBMISSION_POLLING_STEP = 3
SUBMISSION_POLLING_TIMEOUT = 30


class IngestArchiver:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.usi_api = USIAPI()
        self.converter = Converter()

    def archive(self, hca_data):
        summary = self.add_submission_contents(hca_data)
        submission = summary['usi_submission']

        is_validated = polling.poll(
            lambda: self.is_validated(submission),
            step=VALIDATION_POLLING_STEP,
            timeout=VALIDATION_POLLING_TIMEOUT
        )

        is_submittable = self.is_submittable(submission)

        if is_validated and is_submittable:
            self.usi_api.update_submission_status(submission, 'Submitted')
        else:
            validation_summary = self.get_all_validation_result_details(submission)
            summary['validation_summary'] = validation_summary

        is_completed = polling.poll(
            lambda: self.is_processing_complete(submission),
            step=SUBMISSION_POLLING_STEP,
            timeout=SUBMISSION_POLLING_TIMEOUT
        )  # TODO handle timeout error

        summary["is_completed"] = is_completed

        return summary

    def add_submission_contents(self, hca_submission):
        usi_submission = self.usi_api.create_submission()

        get_contents_url = usi_submission['_links']['contents']['href']
        contents = self.usi_api.get_contents(get_contents_url)
        create_sample_url = contents['_links']['samples:create']['href']

        # TODO must know which contents are needed for this archive
        # TODO skip contents which has accessioning input from user
        samples = hca_submission['samples']

        converted_samples = []  # TODO should this be atomic?
        created_samples = []
        hca_samples_by_alias = {}

        for sample in samples:
            converted_sample = None
            try:
                converted_sample = self.converter.convert_sample(sample)
                converted_samples.append(converted_sample)
                alias = converted_sample['alias']
                # build map upon conversion so there'll be no need to do loop twice
                hca_samples_by_alias[alias] = sample
            except ConversionError as e:
                error_message = "Error:" + str(e)
                self.logger.error(error_message)
                pass

            if converted_sample:
                created_usi_sample = self.usi_api.create_sample(create_sample_url, converted_sample)
                created_samples.append(created_usi_sample)

        return {
            "usi_submission": usi_submission,
            "created_samples": created_samples,
            "hca_submission": hca_submission ,
            "hca_samples_by_alias": hca_samples_by_alias,
            "converted_samples": converted_samples
        }
        # TODO Refactor this, there's a lot of things being done here, create an output object
        # TODO do we need to store some of these info somewhere?

    def get_all_validation_result_details(self, usi_submission):
        get_validation_results_url = usi_submission['_links']['validationResults']['href']
        validation_results = self.usi_api.get_validation_results(get_validation_results_url)

        summary = []
        for validation_result in validation_results:
            if validation_result['validationStatus'] == "Complete":
                details_url = validation_result['_links']['validationResult']['href']
                # TODO fix how what to put as projection param, check usi documentation, removing any params for now
                details_url = details_url.split('{')[0]
                validation_result_details = self.usi_api.get_validation_result_details(details_url)
                summary.append(validation_result_details)

        return summary

    def is_submittable(self, usi_submission):
        get_status_url = usi_submission['_links']['submissionStatus']['href']
        submission_status = self.usi_api.get_submission_status(get_status_url)

        get_available_statuses_url = submission_status['_links']['availableStatuses']['href']
        available_statuses = self.usi_api.get_available_statuses(get_available_statuses_url)

        for status in available_statuses:
            if status['statusName'] == 'Submitted':
                return True

        return False

    def is_validated(self, usi_submission):
        get_validation_results_url = usi_submission['_links']['validationResults']['href']
        validation_results = self.usi_api.get_validation_results(get_validation_results_url)

        for validation_result in validation_results:
            if validation_result['validationStatus'] != "Complete":
                return False

        return True

    def is_validated_and_submittable(self, usi_submission):
        return self.is_validated(usi_submission) and self.is_submittable(usi_submission)

    def complete_submission(self, usi_submission):
        if self.is_validated_and_submittable(usi_submission):
            return self.usi_api.update_submission_status(usi_submission, 'Submitted')

        return None

    def is_processing_complete(self, usi_submission):
        results = self.usi_api.get_processing_results(usi_submission)
        for result in results:
            if result['status'] != "Completed":
                return False

        return True

    def delete_submission(self, usi_submission):
        delete_url = usi_submission['_links']['self:delete']['href']
        return self.usi_api.delete_submission(delete_url)

    def get_processing_results(self, usi_submission):
        return self.usi_api.get_processing_results(usi_submission)

