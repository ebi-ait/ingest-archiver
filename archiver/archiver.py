import json
import requests
import logging
import os

from archiver.converter import Converter, ConversionError

# TODO reorganize into separate components
# TODO create config file for env vars
# TODO figure out how to refresh token when it's expired


def get_aap_token(username, password):
    token = None

    get_token_url = 'https://explore.api.aap.tsi.ebi.ac.uk/auth'
    response = requests.get(get_token_url, auth=(username, password))

    if response.ok:
        token = response.text

    return token


class IngestArchiver:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

        aap_user = 'hcaingestd'
        aap_password = ''

        if 'AAP_INGEST_PASSWORD' in os.environ:
            aap_password = os.environ['AAP_INGEST_PASSWORD']

        self.token = get_aap_token(aap_user, aap_password)

        self.headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + self.token
        }

        self.converter = Converter()

    # === external api

    def get_token(self, username, password):
        return get_aap_token(username, password)

    # === usi api methods

    def create_submission(self):
        team = 'self.hca-user'
        create_submissions_url = 'https://submission-dev.ebi.ac.uk/api/teams/' + team + '/submissions'

        submission = None

        response = requests.post(create_submissions_url, data=json.dumps({}), headers=self.headers)

        if response.ok:
            submission = json.loads(response.text)

        return submission

    def delete_submission(self, delete_url):
        is_deleted = self.__delete(delete_url)

        return is_deleted

    def get_contents(self, get_contents_url):
        return self.__get_json(get_contents_url)

    def get_submission_status(self, get_submission_status_url):
        return self.__get_json(get_submission_status_url)

    def create_sample(self, create_sample_url, sample):
        return self.__post(create_sample_url, sample)

    def create_samples(self, create_sample_url, samples):
        for sample in samples:
            converted_sample = self.converter.convert_sample(sample)
            self.create_sample(create_sample_url, converted_sample)

    def get_available_statuses(self, get_available_statuses_url):
        response = self.__get_json(get_available_statuses_url)

        if response and "_embedded" in response:
            return response["_embedded"]["statusDescriptions"]

        return []

    def get_validation_results(self, get_validation_results_url):
        response = self.__get_json(get_validation_results_url)

        if response and "_embedded" in response:
            return response["_embedded"]["validationResults"]

        return []

    def get_validation_result_details(self, get_validation_result_url):
        return self.__get_json(get_validation_result_url)

    def update_submission_status(self, usi_submission, new_status):
        submission_status_url = usi_submission['_links']['submissionStatus']['href']
        status_json = {"status": new_status}

        updated_submission = self.__patch(submission_status_url, status_json)

        return updated_submission

    def get_processing_summary(self, usi_submission):
        get_summary_url = usi_submission['_links']['processingStatusSummary']['href']

        return self.__get_json(get_summary_url)

    def get_processing_results(self, usi_submission):
        get_results_url = usi_submission['_links']['processingStatuses']['href']
        response = self.__get_json(get_results_url)

        if response and "_embedded" in response:
            return response["_embedded"]["processingStatuses"]

        return []

    # ==== archive process methods

    def archive(self, hca_data):
        pass

    def add_submission_contents(self, hca_submission):
        usi_submission = self.create_submission()

        get_contents_url = usi_submission['_links']['contents']['href']
        contents = self.get_contents(get_contents_url)
        create_sample_url = contents['_links']['samples:create']['href']

        # TODO must know which contents are needed for this archiver
        samples = hca_submission['samples']

        converted_samples = []  # TODO should this be atomic? currently there are bad data so ignoring those for now
        created_samples = []
        for sample in samples:
            converted_sample = None
            try:
                converted_sample = self.converter.convert_sample(sample)
                converted_samples.append(converted_sample)
            except ConversionError:
                pass

            if converted_sample:
                created_usi_sample = self.create_sample(create_sample_url, converted_sample)
                created_samples.append(created_usi_sample)

        return {"usi_submission": usi_submission, "created_samples": created_samples}

    # TODO add test
    def get_all_validation_result_details(self, usi_submission):
        get_validation_results_url = usi_submission['_links']['validationResults']['href']
        validation_results = self.get_validation_results(get_validation_results_url)

        summary = []
        for validation_result in validation_results:
            if validation_result['validationStatus'] == "Complete":
                details_url = validation_result['embedded']['_links']['validationResult']
                validation_result_details = self.get_validation_result_details(details_url)
                summary.append(validation_result_details)

        return summary

    def is_submittable(self, usi_submission):
        get_status_url = usi_submission['_links']['submissionStatus']['href']
        submission_status = self.get_submission_status(get_status_url)

        get_available_statuses_url = submission_status['_links']['availableStatuses']['href']
        available_statuses = self.get_available_statuses(get_available_statuses_url)

        if available_statuses:
            for status in available_statuses:
                if status['statusName'] == 'Submitted':
                    return True

        return False

    def is_validated(self, usi_submission):
        get_validation_results_url = usi_submission['_links']['validationResults']['href']
        validation_results = self.get_validation_results(get_validation_results_url)

        for validation_result in validation_results:
            if validation_result['validationStatus'] != "Complete":
                return False

        return True

    def is_validated_and_submittable(self, usi_submission):
        return self.is_validated(usi_submission) and self.is_submittable(usi_submission)

    def complete_submission(self, usi_submission):
        if self.is_validated_and_submittable(usi_submission):
            return self.update_submission_status(usi_submission, 'Submitted')

        return None

    def is_processing_complete(self, usi_submission):
        results = self.get_processing_results(usi_submission)

        for result in results:
            if result['status'] != "Complete":
                return False

        return True

    # TODO add test
    def get_accessions(self, usi_submission):
        results = self.get_processing_results(usi_submission)

        accessions = {}
        for result in results:
            if result['status'] == 'Complete':
                accessions[result['alias']] = result['accession']

        return accessions

    # ===

    def __get_json(self, url):
        response = requests.get(url, headers=self.headers)

        entity = None

        if response.ok:
            entity = json.loads(response.text)
        else:
            self.logger.error('Response:' + response.text)

        return entity

    def __post(self, url, data_json):
        response = requests.post(url, data=json.dumps(data_json), headers=self.headers)

        if response.ok:
            return json.loads(response.text)
        else:
            self.logger.error('Response:' + response.text)

        return None

    def __patch(self, url, data_json):
        response = requests.patch(url, data=json.dumps(data_json), headers=self.headers)

        if response.ok:
            return json.loads(response.text)
        else:
            self.logger.error('Response:' + response.text)

        return None

    def __delete(self, delete_url):
        response = requests.delete(delete_url, headers=self.headers)

        if response.ok:
            return True
        else:
            self.logger.error('Response:' + response.text)

        return False