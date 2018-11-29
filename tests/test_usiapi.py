import unittest
import os
import json
import config

from archiver.usiapi import USIAPI, AAPTokenClient
from archiver.converter import SampleConverter


# TODO use mocks for requests
# TODO add test cases


class TestUSIAPI(unittest.TestCase):
    def setUp(self):
        self.usi_api = USIAPI()

        with open(config.JSON_DIR + 'hca/biomaterials.json', encoding=config.ENCODING) as data_file:
            hca_samples = json.loads(data_file.read())

        self.hca_submission = {'samples': hca_samples}
        self.converter = SampleConverter()
        pass

    def test_get_token_given_valid_credentials_return_token(self):
        aap_user = 'hca-ingest'
        aap_password = os.environ.get('AAP_API_PASSWORD', '')

        token_client = AAPTokenClient(username=aap_user, password=aap_password)
        token = token_client.retrieve_token()

        self.assertTrue(token)

    def test_get_token_given_invalid_credentials_return_none(self):
        username = 'invalid'
        password = 'invalid'

        token_client = AAPTokenClient(username=username, password=password)
        token = token_client.retrieve_token()

        self.assertFalse(token)

    def test_create_submission(self):
        usi_submission = self.usi_api.create_submission()
        print(usi_submission)

        delete_url = usi_submission['_links']['self:delete']['href']
        self.usi_api.delete_submission(delete_url)

        self.assertTrue(usi_submission['_links']['self']['href'])

    def test_get_submission_contents(self):
        usi_submission = self.usi_api.create_submission()

        get_contents_url = usi_submission['_links']['contents']['href']

        contents = self.usi_api.get_contents(get_contents_url)

        delete_url = usi_submission['_links']['self:delete']['href']
        self.usi_api.delete_submission(delete_url)

        self.assertTrue(contents)

    def test_create_sample(self):
        usi_submission = self.usi_api.create_submission()

        get_contents_url = usi_submission['_links']['contents']['href']
        contents = self.usi_api.get_contents(get_contents_url)
        create_sample_url = contents['_links']['samples:create']['href']

        samples = self.hca_submission['samples']
        sample = samples[0]
        sample = {
            'biomaterial': sample
        }

        converted_sample = self.converter.convert(sample)

        created_usi_sample = self.usi_api.create_entity(create_sample_url, converted_sample)

        # clean up submission in USI
        delete_url = usi_submission['_links']['self:delete']['href']
        self.usi_api.delete_submission(delete_url)

        self.assertTrue(created_usi_sample)
