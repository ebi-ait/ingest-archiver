import unittest
import json
import time
import polling as polling
import config

from random import randint

from archiver.archiver import IngestArchiver
from archiver.converter import Converter

# TODO use mocks for requests
# TODO add test cases


class TestIngestArchiver(unittest.TestCase):
    def setUp(self):
        self.archiver = IngestArchiver()
        self.converter = Converter()

        with open(config.JSON_DIR + 'hca-samples.json', encoding=config.ENCODING) as data_file:
            hca_samples = json.loads(data_file.read())

        for sample in hca_samples:
            # TODO decide what to use for alias, assign random no for now
            sample['uuid']['uuid'] = 'hca' + str(randint(0, 1000))

        self.hca_submission = {'samples': hca_samples}

        pass

    def test_add_submission_contents(self):
        summary = self.archiver.add_submission_contents(self.hca_submission)

        self.archiver.delete_submission(summary['usi_submission'])

        self.assertTrue(summary['usi_submission'])
        self.assertTrue(summary['created_samples'])

    def test_is_submittable(self):
        add_summary = self.archiver.add_submission_contents(self.hca_submission)

        time.sleep(3)
        is_submittable = self.archiver.is_submittable(add_summary['usi_submission'])

        self.archiver.delete_submission(add_summary['usi_submission'])

        self.assertTrue(is_submittable)

    def test_is_validated(self):
        add_summary = self.archiver.add_submission_contents(self.hca_submission)

        time.sleep(3)
        is_validated = self.archiver.is_validated(add_summary['usi_submission'])

        self.archiver.delete_submission(add_summary['usi_submission'])

        self.assertTrue(is_validated)

    def test_is_validated_and_submittable(self):
        add_summary = self.archiver.add_submission_contents(self.hca_submission)

        time.sleep(3)
        is_validated_and_submittable = self.archiver.is_validated_and_submittable(add_summary['usi_submission'])

        self.archiver.delete_submission(add_summary['usi_submission'])

        self.assertTrue(is_validated_and_submittable)

    @unittest.skip('submitted submissions cannot be deleted, skipping this')
    def test_archive(self):
        summary = self.archiver.archive(self.hca_submission)
        self.assertTrue(summary["is_completed"])
