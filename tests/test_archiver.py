import copy
import datetime
import json
import unittest

from mock import MagicMock, patch

import config
from archiver.archiver import IngestArchiver, Manifest, ArchiveSubmission, Biomaterial


# TODO use mocks for integration tests
class TestIngestArchiver(unittest.TestCase):
    def setUp(self):
        self.ontology_api = MagicMock()

        self.ingest_api = MagicMock()
        self.ingest_api.url = 'ingest_url'

        self.dsp_api = MagicMock()
        self.dsp_api.url = 'dsp_url'
        self.dsp_api.get_current_version = MagicMock(return_value=None)

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
            library_preparation_protocol['uuid']['uuid'] = self._generate_fake_id(
                prefix='library_preparation_protocol_')

        with open(config.JSON_DIR + 'hca/sequencing_protocol.json', encoding=config.ENCODING) as data_file:
            sequencing_protocol = json.loads(data_file.read())
            sequencing_protocol['uuid']['uuid'] = self._generate_fake_id(prefix='sequencing_protocol_')

        with open(config.JSON_DIR + 'hca/sequencing_file.json', encoding=config.ENCODING) as data_file:
            sequencing_file = json.loads(data_file.read())
            sequencing_file['uuid']['uuid'] = self._generate_fake_id(prefix='sequencing_file_')

        biomaterial_objects = []
        for biomaterial in biomaterials:
            # TODO decide what to use for alias, assign random no for now
            biomaterial['uuid']['uuid'] = self._generate_fake_id(prefix='biomaterial_')
            biomaterial_objects.append(Biomaterial(biomaterial))

        with open(config.JSON_DIR + 'hca/library_preparation_protocol_10x.json', encoding=config.ENCODING) as data_file:
            library_preparation_protocol_10x = json.loads(data_file.read())
            library_preparation_protocol_10x['uuid']['uuid'] = self._generate_fake_id(
                prefix='library_preparation_protocol_10x_')

        self.base_manifest = {
            'biomaterials': biomaterial_objects,
            'project': project,
            'files': [sequencing_file],
            'assay': assay,
            'library_preparation_protocol': library_preparation_protocol,
            'library_preparation_protocol_10x': library_preparation_protocol_10x,
            'sequencing_protocol': sequencing_protocol,
            'input_biomaterial': biomaterials[0],
            'manifest_id': 'dummy_manifest_id'
        }

    def _generate_fake_id(self, prefix):
        now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H%M%S")
        return prefix + '_' + now

    @staticmethod
    def _mock_manifest(manifest):
        assay_manifest = MagicMock(Manifest)
        assay_manifest.get_biomaterials = MagicMock(
            return_value=manifest.get('biomaterials'))
        assay_manifest.get_project = MagicMock(
            return_value=manifest.get('project'))
        assay_manifest.get_assay_process = MagicMock(
            return_value=manifest.get('assay'))
        assay_manifest.get_library_preparation_protocol = MagicMock(
            return_value=manifest.get('library_preparation_protocol'))
        assay_manifest.get_sequencing_protocol = MagicMock(
            return_value=manifest.get('sequencing_protocol'))
        assay_manifest.get_input_biomaterial = MagicMock(
            return_value=manifest.get('input_biomaterial'))
        assay_manifest.get_files = MagicMock(
            return_value=manifest.get('files'))
        assay_manifest.manifest_id = manifest.get('manifest_id')
        return assay_manifest

    def test_archive_skip_metadata_with_accessions(self):
        with open(config.JSON_DIR + 'hca/biomaterial_with_accessions.json', encoding=config.ENCODING) as data_file:
            biomaterials = json.loads(data_file.read())
        biomaterial_manifest = {'biomaterials': biomaterials}
        mock_manifest = self._mock_manifest(biomaterial_manifest)
        archiver = IngestArchiver(
            ontology_api=self.ontology_api,
            ingest_api=self.ingest_api,
            dsp_api=self.dsp_api,
            exclude_types=['sequencingRun'])
        archiver.get_manifest = MagicMock(return_value=mock_manifest)
        entity_map = archiver.convert('')
        archive_submission = archiver.archive(entity_map)

        self.assertTrue(archive_submission.is_completed)
        self.assertTrue(archive_submission.errors)
        self.assertFalse(archive_submission.processing_result)
