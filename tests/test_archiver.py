import json
import time
import unittest
from random import randint
from mock import MagicMock

import config
from archiver.archiver import IngestArchiver, AssayBundle
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
        assay_bundle = MagicMock('assay_bundle')
        assay_bundle.get_biomaterials = MagicMock(
            return_value=self.hca_submission['biomaterials'])
        entities_by_type = self.archiver.get_archivable_entities(assay_bundle)
        self.assertTrue(entities_by_type['sample'])

    def test_is_submittable(self):
        assay_bundle = MagicMock('assay_bundle')
        assay_bundle.get_biomaterials = MagicMock(
            return_value=self.hca_submission['biomaterials'])
        entities_dict_by_type = self.archiver.get_archivable_entities(assay_bundle)
        converted_entities = self.archiver._get_converted_entities(entities_dict_by_type)

        usi_submission = self.usi_api.create_submission()

        self.archiver.add_entities_to_submission(usi_submission, converted_entities)

        time.sleep(3)
        is_submittable = self.archiver.is_submittable(usi_submission)

        self.archiver.delete_submission(usi_submission)

        self.assertTrue(is_submittable)

    def test_is_validated(self):
        assay_bundle = MagicMock('assay_bundle')
        assay_bundle.get_biomaterials = MagicMock(
            return_value=self.hca_submission['biomaterials'])
        entities_dict_by_type = self.archiver.get_archivable_entities(assay_bundle)
        converted_entities = self.archiver._get_converted_entities(entities_dict_by_type)

        usi_submission = self.usi_api.create_submission()

        self.archiver.add_entities_to_submission(usi_submission, converted_entities)

        time.sleep(3)
        is_validated = self.archiver.is_validated(usi_submission)

        self.archiver.delete_submission(usi_submission)

        self.assertTrue(is_validated)

    def test_is_validated_and_submittable(self):
        assay_bundle = MagicMock('assay_bundle')
        assay_bundle.get_biomaterials = MagicMock(
            return_value=self.hca_submission['biomaterials'])
        entities_dict_by_type = self.archiver.get_archivable_entities(assay_bundle)
        converted_entities =  self.archiver._get_converted_entities(entities_dict_by_type)

        usi_submission = self.usi_api.create_submission()

        self.archiver.add_entities_to_submission(usi_submission, converted_entities)

        time.sleep(3)
        is_validated_and_submittable = self.archiver.is_validated_and_submittable(usi_submission)

        self.archiver.delete_submission(usi_submission)

        self.assertTrue(is_validated_and_submittable)

    # @unittest.skip('submitted submissions cannot be deleted, skipping this')
    def test_archive(self):
        assay_bundle = MagicMock('assay_bundle')
        assay_bundle.get_biomaterials = MagicMock(
            return_value=self.hca_submission['biomaterials'])
        entities_dict_by_type = self.archiver.get_archivable_entities(assay_bundle)
        summary = self.archiver.archive(entities_dict_by_type)
        print(str(summary))
        summary.print_entities()
        self.assertTrue(summary.is_completed)
        self.assertTrue(summary.processing_result)

    def test_archive_skip_metadata_with_accessions(self):
        with open(config.JSON_DIR + 'hca/biomaterial_with_accessions.json', encoding=config.ENCODING) as data_file:
            samples = json.loads(data_file.read())
        hca_submission = {'biomaterials': samples}
        assay_bundle = MagicMock('assay_bundle')
        assay_bundle.get_biomaterials = MagicMock(
            return_value=hca_submission['biomaterials'])
        entities_dict_by_type = self.archiver.get_archivable_entities(assay_bundle)
        summary = self.archiver.archive(entities_dict_by_type)
        print(str(summary))
        self.assertTrue(summary.is_completed)
        self.assertFalse(summary.errors)
        self.assertFalse(summary.processing_result)
