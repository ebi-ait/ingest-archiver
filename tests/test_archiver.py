import json
import time
import unittest
from random import randint
from mock import MagicMock

import config
from archiver.archiver import IngestArchiver
from archiver.converter import Converter
from archiver.ingestapi import IngestAPI
from archiver.usiapi import USIAPI


class TestIngestArchiver(unittest.TestCase):
    def setUp(self):
        self.archiver = IngestArchiver()
        self.converter = Converter()
        self.ingest_api = IngestAPI()
        self.usi_api = USIAPI()

        with open(config.JSON_DIR + 'hca/biomaterials.json', encoding=config.ENCODING) as data_file:
            hca_samples = json.loads(data_file.read())

        for sample in hca_samples:
            # TODO decide what to use for alias, assign random no for now
            sample['uuid']['uuid'] = 'hca' + str(randint(0, 1000)) + str(randint(0, 1000))

        self.hca_submission = {
            'biomaterials': hca_samples,
        }

        pass

    def test_get_archivable_entities(self):
        self.archiver.ingest_api.get_biomaterials_in_bundle = MagicMock(
            return_value=self.hca_submission['biomaterials'])
        summary = self.archiver.get_archivable_entities('dummy_uuid')
        self.assertTrue(summary['samples'])

    def test_is_submittable(self):
        self.archiver.ingest_api.get_biomaterials_in_bundle = MagicMock(
            return_value=self.hca_submission['biomaterials'])
        entities_dict_by_type = self.archiver.get_archivable_entities('dummy_bundle_uuid')
        converted_entities = self.archiver._get_converted_entities(entities_dict_by_type)

        usi_submission = self.usi_api.create_submission()

        self.archiver.add_entities_to_submission(usi_submission, converted_entities)

        time.sleep(3)
        is_submittable = self.archiver.is_submittable(usi_submission)

        self.archiver.delete_submission(usi_submission)

        self.assertTrue(is_submittable)

    def test_is_validated(self):
        self.archiver.ingest_api.get_biomaterials_in_bundle = MagicMock(
            return_value=self.hca_submission['biomaterials'])
        entities_dict_by_type = self.archiver.get_archivable_entities('dummy_bundle_uuid')
        converted_entities = self.archiver._get_converted_entities(entities_dict_by_type)

        usi_submission = self.usi_api.create_submission()

        self.archiver.add_entities_to_submission(usi_submission, converted_entities)

        time.sleep(3)
        is_validated = self.archiver.is_validated(usi_submission)

        self.archiver.delete_submission(usi_submission)

        self.assertTrue(is_validated)

    def test_is_validated_and_submittable(self):
        self.archiver.ingest_api.get_biomaterials_in_bundle = MagicMock(
            return_value=self.hca_submission['biomaterials'])
        entities_dict_by_type = self.archiver.get_archivable_entities('dummy_bundle_uuid')
        converted_entities =  self.archiver._get_converted_entities(entities_dict_by_type)

        usi_submission = self.usi_api.create_submission()

        self.archiver.add_entities_to_submission(usi_submission, converted_entities)

        time.sleep(3)
        is_validated_and_submittable = self.archiver.is_validated_and_submittable(usi_submission)

        self.archiver.delete_submission(usi_submission)

        self.assertTrue(is_validated_and_submittable)

    # @unittest.skip('submitted submissions cannot be deleted, skipping this')
    def test_archive(self):
        self.archiver.ingest_api.get_biomaterials_in_bundle = MagicMock(
            return_value=self.hca_submission['biomaterials'])
        entities_dict_by_type = self.archiver.get_archivable_entities('dummy_bundle')
        summary = self.archiver.archive(entities_dict_by_type)
        print(str(summary))
        self.assertTrue(summary.is_completed)
        self.assertTrue(summary.processing_result)

    def test_archive_skip_metadata_with_accessions(self):
        with open(config.JSON_DIR + 'hca/biomaterial_with_accessions.json', encoding=config.ENCODING) as data_file:
            samples = json.loads(data_file.read())
        hca_submission = {'biomaterials': samples}
        self.archiver.ingest_api.get_biomaterials_in_bundle = MagicMock(
            return_value=hca_submission['biomaterials'])
        entities_dict_by_type = self.archiver.get_archivable_entities('dummy_bundle')
        summary = self.archiver.archive(entities_dict_by_type)
        print(str(summary))
        self.assertTrue(summary.is_completed)
        self.assertFalse(summary.errors)
        self.assertFalse(summary.processing_result)
