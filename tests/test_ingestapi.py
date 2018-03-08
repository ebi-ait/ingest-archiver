import unittest
import config
import json

from archiver.ingestapi import IngestAPI


class TestIngestAPI(unittest.TestCase):
    def setUp(self):
        self.ingest_api = IngestAPI()
        pass

    def test_create_submission_no_input_token_success(self):
        token = self.ingest_api.get_auth_token()
        submission = self.ingest_api.create_submission(token)

        if submission:
            submission_url = submission['_links']['self']['href']
            self.ingest_api.delete_submission(submission_url)

        self.assertTrue(submission)

    def test_create_submission_success(self):
        token = self.ingest_api.get_auth_token()
        submission = self.ingest_api.create_submission(token)

        if submission:
            submission_url = submission['_links']['self']['href']
            self.ingest_api.delete_submission(submission_url)

        self.assertTrue(submission)

    def test_create_submission_fail(self):
        invalid_token = {'token_type': 'Bearer', 'access_token': 'invalid'};
        submission = self.ingest_api.create_submission(invalid_token)

        self.assertFalse(submission)

    def test_update_content(self):
        sample_content = {}

        with open(config.JSON_DIR + 'sample-content-v4.json', encoding=config.ENCODING) as data_file:
            sample_content = json.loads(data_file.read())

        token = self.ingest_api.get_auth_token()
        submission = self.ingest_api.create_submission(token)
        sample = self.ingest_api.create_sample(submission, sample_content)

        self.ingest_api.submit_if_valid(submission)

        # update sample in submitted submission
        content_patch = {
            "sample_accessions": {
                "biosd_sample": 'SAMEA4437026'
            }
        }

        sample_url = self.ingest_api.get_link_href(sample, 'self')
        token = self.ingest_api.get_auth_token()
        update_submission = self.ingest_api.create_submission(token)

        new_samples_url = self.ingest_api.get_link_href(update_submission, 'samples')
        new_sample = self.ingest_api.link_samples_to_submission(new_samples_url, sample_url)

        new_sample_url = self.ingest_api.get_link_href(new_sample, 'self')
        updated_sample = self.ingest_api.update_content(new_sample_url, content_patch)

        # create sample
        self.assertEqual(updated_sample['content']['sample_accessions'], content_patch['sample_accessions'])
