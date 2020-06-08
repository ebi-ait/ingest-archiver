from unittest import TestCase

from mock import MagicMock

from archiver.archiver import Manifest, Biomaterial, ArchiverError


class ManifestTest(TestCase):

    def test_get_project(self):
        ingest_api_mock = MagicMock(name='ingest_api')
        ingest_api_mock.get_project_by_uuid = MagicMock(return_value='project')
        ingest_api_mock.get_manifest_by_id = MagicMock(return_value={'fileProjectMap': ['p1']})
        manifest = Manifest(ingest_api_mock, 'manifest_id')
        project = manifest.get_project()
        self.assertEqual(project, 'project')

    def test_get_biomaterials(self):
        ingest_api_mock = MagicMock(name='ingest_api')
        ingest_api_mock.get_manifest_by_id = MagicMock(return_value={'fileBiomaterialMap': ['b1']})
        manifest = Manifest(ingest_api_mock, 'manifest_id')
        biomaterials = manifest.get_biomaterials()
        Biomaterial.from_uuid = MagicMock(return_value='biomaterial')
        self.assertEqual(list(biomaterials), ['biomaterial'])

    def test_get_assay_process(self):
        ingest_api_mock = MagicMock(name='ingest_api')
        ingest_api_mock.get_manifest_by_id = MagicMock(return_value={'fileFilesMap': ['f1']})
        ingest_api_mock.get_file_by_uuid = MagicMock()
        related_entity_map = {
            'derivedByProcesses': iter('p1')
        }
        ingest_api_mock.get_related_entity = lambda f, relationship, t: related_entity_map.get(relationship)
        manifest = Manifest(ingest_api_mock, 'manifest_id')
        assay_process = manifest.get_assay_process()
        self.assertEqual(assay_process, 'p1')

    def test_get_assay_process_multiple_assay_found_error(self):
        ingest_api_mock = MagicMock(name='ingest_api')
        ingest_api_mock.get_manifest_by_id = MagicMock(return_value={'fileFilesMap': ['f1']})
        ingest_api_mock.get_file_by_uuid = MagicMock()
        related_entity_map = {
            'derivedByProcesses': iter(['p1', 'p2'])
        }
        ingest_api_mock.get_related_entity = lambda f, relationship, t: related_entity_map.get(relationship)
        manifest = Manifest(ingest_api_mock, 'manifest_id')

        with self.assertRaises(ArchiverError):
            manifest.get_assay_process()

    def test_get_library_preparation_protocol(self):
        ingest_api_mock = MagicMock(name='ingest_api')
        ingest_api_mock.get_file_by_uuid = MagicMock()
        related_entity_map = {
            'protocols': iter(['p1', 'p2'])
        }
        protocol_map = {
            'p1': 'library_preparation_protocol',
            'p2': 'sequencing_protocol'
        }
        ingest_api_mock.get_related_entity = lambda f, relationship, t: related_entity_map.get(relationship)
        ingest_api_mock.get_concrete_entity_type = lambda protocol: protocol_map.get(protocol)
        manifest = Manifest(ingest_api_mock, 'manifest_id')
        manifest.get_assay_process = MagicMock()

        libprep_protocol = manifest.get_library_preparation_protocol()
        self.assertEqual(libprep_protocol, 'p1')

    def test_get_library_preparation_protocol_multiple_found_error(self):
        ingest_api_mock = MagicMock(name='ingest_api')
        ingest_api_mock.get_file_by_uuid = MagicMock()
        related_entity_map = {
            'protocols': ['p1', 'p2', 'p3', 'p4']
        }
        protocol_map = {
            'p1': 'library_preparation_protocol',
            'p3': 'library_preparation_protocol',
            'p2': 'sequencing_protocol',
            'p4': 'sequencing_protocol'
        }
        ingest_api_mock.get_related_entity = lambda f, relationship, t: related_entity_map.get(relationship)
        ingest_api_mock.get_concrete_entity_type = lambda protocol: protocol_map.get(protocol)
        manifest = Manifest(ingest_api_mock, 'manifest_id')
        manifest.get_assay_process = MagicMock()

        with self.assertRaises(ArchiverError):
            manifest.get_library_preparation_protocol()

    def test_get_sequencing_protocol_multiple_found_error(self):
        ingest_api_mock = MagicMock(name='ingest_api')
        ingest_api_mock.get_file_by_uuid = MagicMock()
        related_entity_map = {
            'protocols': ['p1', 'p2', 'p3', 'p4']
        }
        protocol_map = {
            'p1': 'library_preparation_protocol',
            'p3': 'library_preparation_protocol',
            'p2': 'sequencing_protocol',
            'p4': 'sequencing_protocol'
        }
        ingest_api_mock.get_related_entity = lambda f, relationship, t: related_entity_map.get(relationship)
        ingest_api_mock.get_concrete_entity_type = lambda protocol: protocol_map.get(protocol)
        manifest = Manifest(ingest_api_mock, 'manifest_id')
        manifest.get_assay_process = MagicMock()

        with self.assertRaises(ArchiverError):
            manifest.get_sequencing_protocol()

    def test_get_sequencing_protocol(self):
        ingest_api_mock = MagicMock(name='ingest_api')
        ingest_api_mock.get_file_by_uuid = MagicMock()
        related_entity_map = {
            'protocols': iter(['p1', 'p2'])
        }
        protocol_map = {
            'p1': 'library_preparation_protocol',
            'p2': 'sequencing_protocol'
        }
        ingest_api_mock.get_related_entity = lambda f, relationship, t: related_entity_map.get(relationship)
        ingest_api_mock.get_concrete_entity_type = lambda protocol: protocol_map.get(protocol)
        manifest = Manifest(ingest_api_mock, 'manifest_id')
        manifest.get_assay_process = MagicMock()
        protocol = manifest.get_sequencing_protocol()
        self.assertEqual(protocol, 'p2')

    def test_get_files(self):
        ingest_api_mock = MagicMock(name='ingest_api')
        related_entity_map = {
            'derivedFiles': iter(['f1', 'f2'])
        }
        ingest_api_mock.get_assay_process = MagicMock()
        ingest_api_mock.get_related_entity = lambda f, relationship, t: related_entity_map.get(relationship)
        manifest = Manifest(ingest_api_mock, 'manifest_id')
        manifest.get_assay_process = MagicMock()
        files = manifest.get_files()
        self.assertEqual(files, ['f1', 'f2'])

    def test_get_input_biomaterial(self):
        ingest_api_mock = MagicMock(name='ingest_api')
        related_entity_map = {
            'inputBiomaterials': iter(['b1'])
        }
        ingest_api_mock.get_related_entity = lambda f, relationship, t: related_entity_map.get(relationship)
        manifest = Manifest(ingest_api_mock, 'manifest_id')
        manifest.get_assay_process = MagicMock()
        biomaterial = manifest.get_input_biomaterial()

        self.assertEqual(biomaterial, 'b1')
