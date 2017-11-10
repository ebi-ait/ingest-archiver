import json
import requests
import logging

# TODO this file may be removed if the event will contain all the hca submission details
# if not, this must be integrated with the current ingest api module that other ingest services uses


class IngestAPI:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json',
        }
        self.url = 'http://localhost:8080'  # TODO put this in config per env

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

    # TODO test this
    def update_content(self, entity_url, content_json):
        response = requests.get(entity_url)
        content = self.handle_response(response)
        update = content.update(content_json)
        response = requests.put(entity_url, json.dumps(update))
        return self.handle_response(response)

    def handle_response(self, response):
        if response.ok:
            return json.loads(response.text)
        else:
            self.logger.error('Response:' + response.text)
            return None
