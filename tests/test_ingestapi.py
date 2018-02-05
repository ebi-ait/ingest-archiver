import unittest

from archiver.ingestapi import IngestAPI


class TestIngestAPI(unittest.TestCase):
    def setUp(self):
        self.ingest_api = IngestAPI()
        pass

    def test_create_submission_success(self):
        token = self.ingest_api.get_auth_token()
        submission = self.ingest_api.create_submission(token)
        print(submission)
        self.assertTrue(submission)

    def test_create_submission_fail(self):
        invalid_token = {'token_type': 'Bearer', 'access_token': 'invalid'};
        submission = self.ingest_api.create_submission(invalid_token)
        print(submission)
        self.assertFalse(submission)