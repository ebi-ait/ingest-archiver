import json
import requests
import logging
import config


# TODO figure out how to refresh token when it's expired
def get_aap_token(username, password):
    token = ''

    get_token_url = config.AAP_API_URL
    response = requests.get(get_token_url, auth=(username, password))

    if response.ok:
        token = response.text

    return token

USI_ENTITY_LINK = {
    'study': 'enaStudies',
    'sample': 'samples',
    'sequencingExperiment': 'sequencingExperiments',
    'project': 'projects',
    'sequencingRun': 'sequencingRuns'
}

USI_ENTITY_CURR_VERSION_LINK = {
    'study': 'studies',
    'sample': 'samples',
    'sequencingExperiment': 'assays',
    'project': 'projects',
    'sequencingRun': 'assayData'
}

class USIAPI:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.token = get_aap_token(config.AAP_API_USER, config.AAP_API_PASSWORD)
        self.headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + self.token
        }
        self.url = config.USI_API_URL
        self.logger.info(f'Using {self.url}')
        self.aap_api_domain = config.AAP_API_DOMAIN

    def get_token(self, user, password):
        return get_aap_token(user, password)

    def create_submission(self):
        create_submissions_url = self.url + '/api/teams/' + self.aap_api_domain + '/submissions'
        return self._post(url=create_submissions_url, data_json={})

    def delete_submission(self, delete_url):
        return self._delete(delete_url)

    def get_contents(self, get_contents_url):
        return self._get(get_contents_url)

    def get_entity_url(self, entity_type):
        return USI_ENTITY_LINK[entity_type]

    def get_submission_status(self, get_submission_status_url):
        return self._get(get_submission_status_url)

    def create_entity(self, create_entity_url, content):
        return self._post(create_entity_url, content)

    def create_samples(self, create_sample_url, samples):
        for sample in samples:
            converted_sample = self.converter.convert(sample)
            self.create_entity(create_sample_url, converted_sample)

    def get_available_statuses(self, get_available_statuses_url):
        response = self._get(get_available_statuses_url)
        return self._get_embedded_list(response, 'statusDescriptions')

    def get_validation_results(self, get_validation_results_url):
        response = self._get(get_validation_results_url)
        return self._get_embedded_list(response, 'validationResults')

    def get_validation_result_details(self, get_validation_result_url):
        return self._get(get_validation_result_url)

    def update_submission_status(self, usi_submission, new_status):
        submission_status_url = usi_submission['_links']['submissionStatus']['href']
        status_json = {"status": new_status}

        updated_submission = self._patch(submission_status_url, status_json)

        return updated_submission

    def get_processing_summary(self, usi_submission):
        get_summary_url = usi_submission['_links']['processingStatusSummary']['href']

        return self._get(get_summary_url)

    def get_processing_results(self, usi_submission):
        get_results_url = usi_submission['_links']['processingStatuses']['href']
        response = self._get(get_results_url)

        return self._get_embedded_list(response, 'processingStatuses')

    def get_current_version(self, entity_type, alias):
        entity_link = USI_ENTITY_CURR_VERSION_LINK[entity_type]
        url = f'{self.url}/api/{entity_link}/search/current-version?teamName={self.aap_api_domain}&alias={alias}'
        response = requests.get(url, headers=self.headers)

        if response.status_code == requests.codes.not_found:
            return None
        elif response.status_code == requests.codes.ok:
            return response.json()
        else:
            response.raise_for_status()

    # ===

    def _get(self, url):
        response = requests.get(url, headers=self.headers)
        return self._get_json(response)

    def _post(self, url, data_json):
        response = requests.post(url, data=json.dumps(data_json), headers=self.headers)
        return self._get_json(response)

    def _patch(self, url, data_json):
        response = requests.patch(url, data=json.dumps(data_json), headers=self.headers)
        return self._get_json(response)

    def _delete(self, delete_url):
        response = requests.delete(delete_url, headers=self.headers)

        if response.ok:
            return True
        else:
            self.logger.error('Response:' + response.text)

        return False

    def _get_json(self, response):
        response.raise_for_status()
        return response.json()

    def _get_embedded_list(self, response, list_name):
        if response and "_embedded" in response:
            return response["_embedded"][list_name]
        return []
