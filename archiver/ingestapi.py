import json
import requests
import logging
import config
import polling

# TODO this file may be removed if the event will contain all the hca submission details
# if not, this must be integrated with the current ingest api module that other ingest services uses

AUTH0_PARAMS = {
    "client_id": "Zdsog4nDAnhQ99yiKwMQWAPc2qUDlR99",
    "client_secret": "t-OAE-GQk_nZZtWn-QQezJxDsLXmU7VSzlAh9cKW5vb87i90qlXGTvVNAjfT9weF",
    "audience": "http://localhost:8080",
    "grant_type": "client_credentials"
}

AUTH0_URL = 'https://danielvaughan.eu.auth0.com/oauth/token'


class IngestAPI:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.headers = {
            'Content-type': 'application/json',
        }
        self.url = config.INGEST_API_URL

    def get_submission_by_id(self, submission_id):
        get_submission_url = self.url + '/submissionEnvelopes/' + submission_id

        response = requests.get(get_submission_url, headers=self.headers)

        submission = None

        if response.ok:
            submission = json.loads(response.text)

        return submission

    def get_submission_by_uuid(self, uuid):
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
        submission = self.get_submission_by_uuid(submission_uuid)

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

    def create_submission(self, auth_token):
        if not auth_token:
            auth_token = self.get_auth_token()

        token_type = auth_token['token_type']
        access_token = auth_token['access_token']

        auth_header = f"{token_type} {access_token}"

        headers = {
            'Content-type': 'application/json',
            'Authorization': auth_header
        }

        links = self.get_ingest_links()
        create_submission_url = links['submissionEnvelopes']['href'].rsplit("{")[0]

        response = requests.post(create_submission_url, headers=headers, data='{}')

        return self.handle_response(response)

    def delete_submission(self, submission_url):
        response = requests.delete(submission_url, headers=self.headers)
        response.raise_for_status()

    def get_ingest_links(self):
        response = requests.get(self.url, headers=self.headers)
        ingest = self.handle_response(response)

        if ingest:
            return ingest["_links"]

        return None

    def link_samples_to_submission(self, link_url, sample_url):
        sample_id = sample_url.split('/')[-1]
        link_url = link_url + '/' + sample_id
        response = requests.put(link_url, headers=self.headers)

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

    def get_auth_token(self):
        response = requests.post(AUTH0_URL,
                                 data=json.dumps(AUTH0_PARAMS),
                                 headers={'Content-type': 'application/json'})
        response.raise_for_status()
        data = response.json()

        return data

    def get_link_href(self, hal_response, link_name):
        link = hal_response['_links'][link_name]
        return link['href'].rsplit("{")[0] if link else ''

    def create_sample(self, submission, content):
        samples_url = self.get_link_href(submission, 'samples')

        response = requests.post(samples_url,
                                 data=json.dumps(content),
                                 headers=self.headers)

        response.raise_for_status()
        return response.json()

    def submit_if_valid(self, submission):
        try:
            submit_url = polling.poll(
                lambda: self.get_submit_url(submission),
                step=5,
                timeout=60
            )
            self.submit(submit_url)
        except polling.TimeoutException:
            self.logger.error("Failed to do an update submission. The submission takes too long to get " +
                              "validated and couldn't be submitted.")
