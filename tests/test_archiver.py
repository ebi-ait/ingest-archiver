import copy
import datetime
import json
import time
import unittest
from random import randint
from mock import MagicMock

import config
from archiver.archiver import IngestArchiver, AssayBundle, ArchiveEntityAggregator, ArchiveEntityMap
from archiver.converter import Converter
from archiver.ingestapi import IngestAPI
from archiver.usiapi import USIAPI


class TestIngestArchiver(unittest.TestCase):
    def setUp(self):
        self.converter = Converter()
        self.ingest_api = IngestAPI()
        self.usi_api = USIAPI()
        self.archiver = IngestArchiver(
            ingest_api=self.ingest_api,
            usi_api=self.usi_api,
            exclude_types=['sequencing_run'])

        with open(config.JSON_DIR + 'hca/biomaterials.json', encoding=config.ENCODING) as data_file:
            biomaterials = json.loads(data_file.read())

        with open(config.JSON_DIR + 'hca/project.json', encoding=config.ENCODING) as data_file:
            project = json.loads(data_file.read())
            project['uuid']['uuid'] = self._generate_fake_id(prefix='project_')

        with open(config.JSON_DIR + 'hca/process.json', encoding=config.ENCODING) as data_file:
            assay = json.loads(data_file.read())
            assay['uuid']['uuid'] = self._generate_fake_id(prefix='assay_')

        with open(config.JSON_DIR + 'hca/library_preparation_protocol.json', encoding=config.ENCODING) as data_file:
            library_preparation_protocol = json.loads(data_file.read())
            library_preparation_protocol['uuid']['uuid'] = self._generate_fake_id(prefix='library_preparation_protocol_')

        with open(config.JSON_DIR + 'hca/sequencing_protocol.json', encoding=config.ENCODING) as data_file:
            sequencing_protocol = json.loads(data_file.read())
            sequencing_protocol['uuid']['uuid'] = self._generate_fake_id(prefix='sequencing_protocol_')

        with open(config.JSON_DIR + 'hca/sequencing_file.json', encoding=config.ENCODING) as data_file:
            sequencing_file = json.loads(data_file.read())
            sequencing_file['uuid']['uuid'] = self._generate_fake_id(prefix='sequencing_file_')

        for biomaterial in biomaterials:
            # TODO decide what to use for alias, assign random no for now
            biomaterial['uuid']['uuid'] = self._generate_fake_id(prefix='biomaterial_')

        with open(config.JSON_DIR + 'hca/library_preparation_protocol_10x.json', encoding=config.ENCODING) as data_file:
            library_preparation_protocol_10x = json.loads(data_file.read())
            library_preparation_protocol_10x['uuid']['uuid'] = self._generate_fake_id(prefix='library_preparation_protocol_10x_')

        self.bundle = {
            'biomaterials': biomaterials,
            'project': project,
            'files': [sequencing_file],
            'assay': assay,
            'library_preparation_protocol': library_preparation_protocol,
            'library_preparation_protocol_10x': library_preparation_protocol_10x,
            'sequencing_protocol': sequencing_protocol,
            'input_biomaterial': biomaterials[0]
        }

    def _generate_fake_id(self, prefix):
        now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H%M%S")
        return prefix + '_' + now

    @unittest.skip("reason for skipping")
    def test_get_archivable_entities(self):
        assay_bundle = self._mock_assay_bundle(self.bundle)
        entity_map = self.archiver.convert(assay_bundle)
        entities_by_type = entity_map.entities_dict_type
        self.assertTrue(entities_by_type['project'])
        self.assertTrue(entities_by_type['study'])
        self.assertTrue(entities_by_type['sample'])
        self.assertTrue(entities_by_type['sequencing_experiment'])

    @unittest.skip("reason for skipping")
    def test_archive(self):
        assay_bundle = self._mock_assay_bundle(self.bundle)
        entity_map = self.archiver.convert(assay_bundle)
        archive_submission = self.archiver.archive(entity_map)
        self.assertTrue(archive_submission.is_completed)

        for type, entity_dict in archive_submission.entities_dict_type.items():
            for id, entity in entity_dict.items():
                self.assertTrue(entity.accession, f"{entity.id} has no accession.")

    def test_notify_file_archiver(self):
        archive_submission = MagicMock()
        archive_submission.get_url = MagicMock(return_value='url')

        assay_bundle = self._mock_assay_bundle(self.bundle)
        assay_bundle.get_library_preparation_protocol = MagicMock(
            return_value=self.bundle.get('library_preparation_protocol_10x'))
        seq_files = self.bundle.get('files')
        seq_file = copy.deepcopy(seq_files[0])
        seq_file['content']['file_core']['file_name'] = "R2.fastq.gz"
        seq_files.append(seq_file)
        assay_bundle.get_files = MagicMock(
            return_value=seq_files)

        ingest_api = MagicMock()
        ingest_api.url = 'ingest_url'
        usi_api = MagicMock()
        usi_api.url = 'usi_url'
        usi_api.get_current_version = MagicMock(return_value=None)

        archiver = IngestArchiver(ingest_api, usi_api)
        entity_map = archiver.convert(assay_bundle)
        entity_map.bundle_uuid = 'bundle_uuid'
        archive_submission.converted_entities = list(entity_map.get_converted_entities())
        archive_submission.entity_map = entity_map

        messages = archiver.notify_file_archiver(archive_submission)

        expected = {
            "usi_api_url": 'usi_url',
            'ingest_api_url': 'ingest_url',
            'submission_url': 'url',
            'files': ['R1.fastq.gz', 'R2.fastq.gz'],
            'conversion': {
                'output_name': 'bundle_uuid.bam',
                'inputs': ['R1.fastq.gz', 'R2.fastq.gz']
            },
            'bundle_uuid': "bundle_uuid"
        }
        self.assertTrue(messages)
        self.assertEqual(expected, messages[0])

    @unittest.skip("reason for skipping")
    def test_validate_and_complete_submission(self):
        assay_bundle = self._mock_assay_bundle(self.bundle)
        entity_map = self.archiver.convert(assay_bundle)
        archive_submission = self.archiver.archive_metadata(entity_map)
        url = archive_submission.get_url()

        archive_submission = self.archiver.validate_and_complete_submission(usi_submission_url=url)
        self.assertTrue(archive_submission.is_completed)

        for type, entity_dict in archive_submission.entities_dict_type.items():
            for id, entity in entity_dict.items():
                self.assertTrue(entity.accession, f"{entity.id} has no accession.")

    # @unittest.skip("reason for skipping")
    def _mock_assay_bundle(self, bundle):
        assay_bundle = MagicMock('assay_bundle')
        assay_bundle.get_biomaterials = MagicMock(
            return_value=bundle.get('biomaterials'))
        assay_bundle.get_project = MagicMock(
            return_value=bundle.get('project'))
        assay_bundle.get_assay_process = MagicMock(
            return_value=bundle.get('assay'))
        assay_bundle.get_library_preparation_protocol = MagicMock(
            return_value=bundle.get('library_preparation_protocol'))
        assay_bundle.get_sequencing_protocol = MagicMock(
            return_value=bundle.get('sequencing_protocol'))
        assay_bundle.get_input_biomaterial = MagicMock(
            return_value=bundle.get('input_biomaterial'))
        assay_bundle.get_files = MagicMock(
            return_value=bundle.get('files'))
        assay_bundle.bundle_uuid = 'bundle_uuid'
        return assay_bundle

    @unittest.skip("reason for skipping")
    def test_archive_skip_metadata_with_accessions(self):
        with open(config.JSON_DIR + 'hca/biomaterial_with_accessions.json', encoding=config.ENCODING) as data_file:
            biomaterials = json.loads(data_file.read())
        bundle = {'biomaterials': biomaterials}
        assay_bundle = self._mock_assay_bundle(bundle)
        entity_map = self.archiver.convert(assay_bundle)
        archive_submission = self.archiver.archive(entity_map)

        self.assertTrue(archive_submission.is_completed)
        self.assertTrue(archive_submission.errors)
        self.assertFalse(archive_submission.processing_result)
