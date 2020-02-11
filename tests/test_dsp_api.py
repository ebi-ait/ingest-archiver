import unittest
import os
import json
import config

from mock import MagicMock
from api.dsp import DataSubmissionPortal, AAPTokenClient
from archiver.converter import SampleConverter


# TODO use mocks for requests
# TODO add test cases

class TestDataSubmissionPortal(unittest.TestCase):
    def setUp(self):
        self.dsp_api = DataSubmissionPortal()

        with open(config.JSON_DIR + 'hca/biomaterials.json', encoding=config.ENCODING) as data_file:
            hca_samples = json.loads(data_file.read())

        self.hca_submission = {'samples': hca_samples}
        self.ontology_api = MagicMock()
        self.ontology_api.expand_curie = MagicMock(return_value='http://purl.obolibrary.org/obo/UO_0000015')

        self.ingest_api = MagicMock()
        self.ingest_api.url = 'ingest_url'
        self.ingest_api.get_concrete_entity_type = MagicMock(return_value='donor_organism')

        self.converter = SampleConverter(ontology_api=self.ontology_api)
        self.converter.ingest_api = self.ingest_api
        pass

    def tearDown(self):
        self.dsp_api.session.close()

    def test_get_token_given_valid_credentials_return_token(self):
        aap_user = os.environ.get('AAP_API_USER', '')
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
        submission = self.dsp_api.create_submission()

        delete_url = submission['_links']['self:delete']['href']
        self.dsp_api.delete_submission(delete_url)

        self.assertTrue(submission['_links']['self']['href'])

    def test_get_submission_contents(self):
        submission = self.dsp_api.create_submission()

        get_contents_url = submission['_links']['contents']['href']

        contents = self.dsp_api.get_contents(get_contents_url)

        delete_url = submission['_links']['self:delete']['href']
        self.dsp_api.delete_submission(delete_url)

        self.assertTrue(contents)

    def test_create_sample(self):
        submission = self.dsp_api.create_submission()

        get_contents_url = submission['_links']['contents']['href']
        contents = self.dsp_api.get_contents(get_contents_url)
        create_sample_url = contents['_links']['samples:create']['href']

        samples = self.hca_submission['samples']
        sample = samples[0]
        sample = {
            'biomaterial': sample
        }

        converted_sample = self.converter.convert(sample)

        created_sample = self.dsp_api.create_entity(create_sample_url, converted_sample)

        # clean up submission in DSP
        delete_url = submission['_links']['self:delete']['href']
        self.dsp_api.delete_submission(delete_url)

        self.assertTrue(created_sample)
