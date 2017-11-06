import unittest
import os
import json
import time

from archiver.archiver import IngestArchiver
from archiver.converter import Converter

# TODO use mocks for requests
# TODO add test cases

JSON_DIR = 'tests/json/'
ENCODING = 'utf-8'


class TestIngestArchiver(unittest.TestCase):
    def setUp(self):
        self.archiver = IngestArchiver()
        self.converter = Converter()

        with open(JSON_DIR + 'hca-samples.json', encoding=ENCODING) as data_file:
            hca_samples = json.loads(data_file.read())

        self.hca_submission = {'samples': hca_samples}

        pass

    def test_get_token_given_valid_credentials_return_token(self):
        aap_user = 'hcaingestd'
        aap_password = 'invalidpass'

        if 'AAP_INGEST_PASSWORD' in os.environ:
            aap_password = os.environ['AAP_INGEST_PASSWORD']

        token = self.archiver.get_token(aap_user, aap_password)

        self.assertTrue(token)

    def test_get_token_given_invalid_credentials_return_none(self):
        username = 'invalid'
        password = 'invalid'

        token = self.archiver.get_token(username, password)

        self.assertFalse(token)

    def test_create_submission(self):
        usi_submission = self.archiver.create_submission()
        print(usi_submission)

        delete_url = usi_submission['_links']['self:delete']['href']
        self.archiver.delete_submission(delete_url)

        self.assertTrue(usi_submission['_links']['self']['href'])

    def test_get_submission_contents(self):
        usi_submission = self.archiver.create_submission()

        get_contents_url = usi_submission['_links']['contents']['href']

        contents = self.archiver.get_contents(get_contents_url)

        delete_url = usi_submission['_links']['self:delete']['href']
        self.archiver.delete_submission(delete_url)

        self.assertTrue(contents)

    def test_create_sample(self):
        usi_submission = self.archiver.create_submission()

        get_contents_url = usi_submission['_links']['contents']['href']
        contents = self.archiver.get_contents(get_contents_url)
        create_sample_url = contents['_links']['samples:create']['href']

        samples = self.hca_submission['samples']
        sample = samples[0]

        converted_sample = self.converter.convert_sample(sample)

        created_usi_sample = self.archiver.create_sample(create_sample_url, converted_sample)

        # clean up submission in USI
        delete_url = usi_submission['_links']['self:delete']['href']
        self.archiver.delete_submission(delete_url)

        self.assertTrue(created_usi_sample)

    def test_add_submission_contents(self):

        summary = self.archiver.add_submission_contents(self.hca_submission)

        # clean up submission in USI
        delete_url = summary['usi_submission']['_links']['self:delete']['href']
        self.archiver.delete_submission(delete_url)

        self.assertTrue(summary['usi_submission'])
        self.assertTrue(summary['created_samples'])

    def test_is_submittable(self):
        add_summary = self.archiver.add_submission_contents(self.hca_submission)

        time.sleep(3)
        is_submittable = self.archiver.is_submittable(add_summary['usi_submission'])

        # clean up submission in USI
        delete_url = add_summary['usi_submission']['_links']['self:delete']['href']
        self.archiver.delete_submission(delete_url)

        self.assertTrue(is_submittable)

    def test_is_validated(self):
        add_summary = self.archiver.add_submission_contents(self.hca_submission)

        time.sleep(3)
        is_validated = self.archiver.is_validated(add_summary['usi_submission'])

        # clean up submission in USI
        delete_url = add_summary['usi_submission']['_links']['self:delete']['href']
        self.archiver.delete_submission(delete_url)

        self.assertTrue(is_validated)

    def test_is_validated_and_submittable(self):
        add_summary = self.archiver.add_submission_contents(self.hca_submission)

        time.sleep(3)
        is_validated_and_submittable = self.archiver.is_validated_and_submittable(add_summary['usi_submission'])

        # clean up submission in USI
        delete_url = add_summary['usi_submission']['_links']['self:delete']['href']
        self.archiver.delete_submission(delete_url)

        self.assertTrue(is_validated_and_submittable)

    @unittest.skip('submitted submissions cannot be deleted, skipping this for now')
    def test_update_submission_status(self):
        add_summary = self.archiver.add_submission_contents(self.hca_submission)
        submission = add_summary['usi_submission']
        time.sleep(3)
        updated_submission = self.archiver.update_submission_status(submission, 'Submitted')

        # clean up submission in USI
        delete_url = submission['_links']['self:delete']['href']
        self.archiver.delete_submission(delete_url)

        self.assertTrue(updated_submission)
        self.assertEqual(updated_submission['status'], 'Submitted')

    @unittest.skip('submitted submissions cannot be deleted, skipping this for now')
    def test_get_processing_summary(self):
        add_summary = self.archiver.add_submission_contents(self.hca_submission)
        submission = add_summary['usi_submission']

        time.sleep(5)
        updated = self.archiver.complete_submission(submission)

        time.sleep(10)
        processing_summary = self.archiver.get_processing_summary(submission)

        self.assertTrue(is_deleted)
        self.assertTrue(processing_summary)
