import json
import logging
import config

import requests
from requests import adapters
from urllib3.util import retry

from utils.token_manager import TokenManager


class AAPTokenClient:
    def __init__(self, url=None, username=None, password=None):
        self.url = url if url else config.AAP_API_URL
        self.username = username if username else config.AAP_API_USER
        self.password = password if password else config.AAP_API_PASSWORD

    def retrieve_token(self):
        token = ''
        response = requests.get(self.url, auth=(self.username, self.password))
        if response.ok:
            token = response.text
        return token


DSP_ENTITY_LINK = {
    'study': 'enaStudies',
    'sample': 'samples',
    'sequencingExperiment': 'sequencingExperiments',
    'project': 'projects',
    'sequencingRun': 'sequencingRuns'
}

DSP_ENTITY_CURR_VERSION_LINK = {
    'study': 'studies',
    'sample': 'samples',
    'sequencingExperiment': 'assays',
    'project': 'projects',
    'sequencingRun': 'assayData'
}


class DataSubmissionPortal:
    def __init__(self, url=None):
        self.logger = logging.getLogger(__name__)
        self.url = url if url else config.DSP_API_URL
        self.logger.info(f'Using {self.url}')

        self.aap_api_domain = config.AAP_API_DOMAIN
        self.token_client = AAPTokenClient(url=config.AAP_API_URL)
        self.token_manager = TokenManager(token_client=self.token_client)
        retry_policy = retry.Retry(
            total=100,  # seems that this has a default value of 10,
            # setting this to a very high number so that it'll respect the status retry count
            status=17,  # status is the no. of retries if response is in status_forcelist,
            # this count will retry for ~20mins with back off timeout within
            read=10,
            status_forcelist=[500, 502, 503, 504],
            backoff_factor=0.6)
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(max_retries=retry_policy)
        self.session.mount('https://', adapter)

    def get_headers(self):
        return {
            'Content-type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + self.token_manager.get_token()
        }

    def create_submission(self):
        create_submissions_url = self.url + '/api/teams/' + self.aap_api_domain + '/submissions'
        return self._post(url=create_submissions_url, data_json={})

    def get_submission(self, url):
        return self._get(url=url)

    def delete_submission(self, delete_url):
        return self._delete(delete_url)

    def get_contents(self, get_contents_url):
        return self._get(get_contents_url)

    def get_entity_url(self, entity_type):
        return DSP_ENTITY_LINK[entity_type]

    def get_submission_status(self, get_submission_status_url):
        return self._get(get_submission_status_url)

    def create_entity(self, create_entity_url, content):
        return self._post(create_entity_url, content)

    def create_samples(self, create_sample_url, samples):
        for sample in samples:
            converted_sample = self.converter.convert(sample)
            self.create_entity(create_sample_url, converted_sample)

    def get_available_statuses(self, get_available_statuses_url):
        return self._get_all(get_available_statuses_url, 'statusDescriptions')

    def get_validation_results(self, get_validation_results_url):
        return self._get_all(get_validation_results_url, 'validationResults')

    def get_validation_result_details(self, get_validation_result_url):
        return self._get(get_validation_result_url)

    def update_submission_status(self, dsp_submission, new_status):
        submission_status_url = dsp_submission['_links']['submissionStatus']['href']
        status_json = {"status": new_status}

        updated_submission = self._patch(submission_status_url, status_json)

        return updated_submission

    def get_processing_summary(self, dsp_submission):
        get_summary_url = dsp_submission['_links']['processingStatusSummary']['href']

        return self._get(get_summary_url)

    def get_processing_results(self, dsp_submission):
        get_results_url = dsp_submission['_links']['processingStatuses']['href']
        return self._get_all(get_results_url, 'processingStatuses')

    def get_current_version(self, entity_type, alias):
        entity_link = DSP_ENTITY_CURR_VERSION_LINK[entity_type]
        url = f'{self.url}/api/{entity_link}/search/current-version?teamName={self.aap_api_domain}&alias={alias}'
        response = self.session.get(url, headers=self.get_headers())

        if response.status_code == requests.codes.not_found:
            return None
        elif response.status_code == requests.codes.ok:
            return response.json()
        else:
            response.raise_for_status()

    # ===

    def _get(self, url):
        response = self.session.get(url, headers=self.get_headers())
        return self._get_json(response)

    def _post(self, url, data_json):
        response = self.session.post(url, data=json.dumps(data_json), headers=self.get_headers())
        return self._get_json(response)

    def _patch(self, url, data_json):
        response = self.session.patch(url, data=json.dumps(data_json), headers=self.get_headers())
        return self._get_json(response)

    def _delete(self, delete_url):
        response = self.session.delete(delete_url, headers=self.get_headers())

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

    def _get_all(self, url, entity_type):
        r = self.session.get(url, headers=self.get_headers())
        r.raise_for_status()
        if "_embedded" in r.json():
            for entity in r.json()["_embedded"][entity_type]:
                yield entity
            while "next" in r.json()["_links"]:
                r = self.session.get(r.json()["_links"]["next"]["href"], headers=self.get_headers())
                for entity in r.json()["_embedded"][entity_type]:
                    yield entity
