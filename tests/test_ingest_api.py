import time
import unittest

import requests

import config
import json

from archiver.ingest_api import IngestAPI


class TestIngestAPI(unittest.TestCase):
    def setUp(self):
        self.ingest_api = IngestAPI()
        pass

    @unittest.skip("update submission is not being done at the moment")
    def test_create_submission_no_input_token_success(self):
        token = self.ingest_api.get_auth_token()
        submission = self.ingest_api.create_submission(token)

        if submission:
            submission_url = submission['_links']['self']['href']
            self.ingest_api.delete_submission(submission_url)

        self.assertTrue(submission)

    @unittest.skip("update submission is not being done at the moment")
    def test_create_submission_success(self):
        token = self.ingest_api.get_auth_token()
        submission = self.ingest_api.create_submission(token)

        if submission:
            submission_url = submission['_links']['self']['href']
            self.ingest_api.delete_submission(submission_url)

        self.assertTrue(submission)

    @unittest.skip("update submission is not being done at the moment")
    def test_create_submission_fail(self):
        invalid_token = {'token_type': 'Bearer', 'access_token': 'invalid'};
        self.assertRaises(requests.exceptions.HTTPError, self.ingest_api.create_submission, invalid_token)

    @unittest.skip("update submission is not being done at the moment")
    def test_update_content(self):
        sample_content = {}

        with open(config.JSON_DIR + 'hca/biomaterial_content.json', encoding=config.ENCODING) as data_file:
            sample_content = json.loads(data_file.read())

        token = self.ingest_api.get_auth_token()
        submission = self.ingest_api.create_submission(token)
        sample = self.ingest_api.create_sample(submission, sample_content)

        self.ingest_api.submit_if_valid(submission)

        # update sample in submitted submission
        sample_content['biomaterial_core']['biosd_biomaterial'] = 'SAMEA5100429'

        time.sleep(3)

        sample_url = self.ingest_api.get_link_href(sample, 'self')
        token = self.ingest_api.get_auth_token()
        update_submission = self.ingest_api.create_submission(token)

        new_samples_url = self.ingest_api.get_link_href(update_submission, 'biomaterials')
        new_sample = self.ingest_api.link_samples_to_submission(new_samples_url, sample_url)

        new_sample_url = self.ingest_api.get_link_href(new_sample, 'self')
        updated_sample = self.ingest_api.update_content(new_sample_url, sample_content)

        # create sample
        self.assertEqual(updated_sample['content']['biomaterial_core']['biosd_biomaterial'], sample_content['biomaterial_core']['biosd_biomaterial'])
