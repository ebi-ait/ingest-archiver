import json
import requests
import logging
import config

# TODO this file may be removed if the event will contain all the hca submission details
# if not, this must be integrated with the current ingest api module that other ingest services uses


class IngestAPI:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.headers = {
            'Content-type': 'application/json',
            # 'Accept': 'application/json',
        }
        self.url = config.INGEST_API_URL

    def get_submission(self, uuid):
        get_submission_url = self.url + '/submissionEnvelopes/search/findByUuid?uuid=' + uuid

        response = requests.get(get_submission_url, headers=self.headers)

        submission = None

        if response.ok:
            submission = json.loads(response.text)

        return submission

    def get_samples(self, get_samples_url):
        response = requests.get(get_samples_url, headers=self.headers)

        samples = []

        if response.ok:
            samples = json.loads(response.text)["_embedded"]["samples"]

        return samples

    def get_samples_by_submission(self, submission_uuid):
        submission = self.get_submission(submission_uuid)

        samples = []

        if submission:
            get_samples_url = submission["_links"]["samples"]["href"]
            samples = self.get_samples(get_samples_url)

        return samples

    def update_content(self, entity_url, content_json):
        response = requests.get(entity_url)
        content = self.handle_response(response)['content']
        content.update(content_json)
        response = requests.put(entity_url, json.dumps(content))

        return self.handle_response(response)

    def handle_response(self, response):
        if response.ok:
            return json.loads(response.text)
        else:
            self.logger.error('Response:' + response.text)
            return None

    def create_submission(self):
        links = self.get_ingest_links()
        create_submission_url = links['submissionEnvelopes']['href'].rsplit("{")[0]
        response = requests.post(create_submission_url, headers=self.headers, data='{}')

        return self.handle_response(response)

    def get_ingest_links(self):
        response = requests.get(self.url, headers=self.headers)
        ingest = self.handle_response(response)

        if ingest:
            return ingest["_links"]

        return None

    def link_samples_to_submission(self, link_url, samples):
        sample_reference = {"uuids": samples}
        response = requests.put(link_url, headers=self.headers, data=json.dumps(sample_reference))

        return self.handle_response(response)

    def get_submit_url(self, submission):
        submission_url = submission['_links']['self']['href']
        response = requests.get(submission_url, headers=self.headers)
        submission = self.handle_response(response)

        if submission and 'submit' in submission['_links']:
            return submission['_links']["submit"]["href"].rsplit("{")[0]

        return None

    def submit(self, submit_url):
        response = requests.put(submit_url, headers=self.headers)

        return self.handle_response(response)
