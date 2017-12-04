import json
import time
import unittest
from random import randint

import config
from archiver.archiver import IngestArchiver
from archiver.converter import Converter
from archiver.ingestapi import IngestAPI

# TODO use mocks for requests
# TODO add test cases


class TestIngestArchiver(unittest.TestCase):
    def setUp(self):
        self.archiver = IngestArchiver()
        self.converter = Converter()
        self.ingest_api = IngestAPI()

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

    # @unittest.skip('submitted submissions cannot be deleted, skipping this')
    def test_archive(self):
        summary = self.archiver.archive(self.hca_submission)

        self.assertTrue(summary["is_completed"])
        self.assertTrue(summary["processing_results"])

    def test_archive_skip_metadata_with_accessions(self):
        with open(config.JSON_DIR + 'hca-samples-with-accessions.json', encoding=config.ENCODING) as data_file:
            samples = json.loads(data_file.read())
        hca_submission = {'samples': samples}
        summary = self.archiver.archive(hca_submission)

        self.assertTrue(summary["is_completed"])
        self.assertFalse(summary["converted_samples"])
        self.assertFalse(summary["created_samples"])
