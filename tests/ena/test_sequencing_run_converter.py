import tempfile
from unittest import TestCase
from unittest.mock import MagicMock, patch, Mock

from ena.sequencing_run_converter import SequencingRunConverter
from ena.util import load_json, load_xml, write_xml


class TestSequencingRunDataConverter(TestCase):
    def setUp(self) -> None:
        self.ingest_api = MagicMock()
        self.run_converter = SequencingRunConverter(self.ingest_api)
        self.temp_dir = tempfile.TemporaryDirectory()
        self.actual_dir = self.temp_dir.name
        self.expected_dir = 'data'

        mock_manifest = self._create_mock_manifest()
        self.run_converter.get_manifest = Mock(return_value=mock_manifest)

    def test_prepare_sequencing_run_data(self):
        # given
        md5_file = f'{self.expected_dir}/md5.txt'
        manifest_id = '60f2a4a6d5d575160aafb78f'

        # when
        run_data = self.run_converter.prepare_sequencing_run_data(manifest_id, md5_file)

        expected_run_data = load_json(f'{self.expected_dir}/sequencing_run_data.json')

        # then
        self.assertEqual(run_data, expected_run_data)

    def test_prepare_sequencing_run_data__in_root_dir(self):
        # given
        md5_file = f'{self.expected_dir}/md5.txt'
        manifest_id = '60f2a4a6d5d575160aafb78f'

        # when
        run_data = self.run_converter.prepare_sequencing_run_data(manifest_id, md5_file, True)

        expected_run_data = load_json(f'{self.expected_dir}/sequencing_run_data__no_dir.json')

        # then
        self.assertEqual(run_data, expected_run_data)

    def _create_mock_manifest(self):
        mock_manifest = Mock()
        mock_manifest.get_submission_uuid.return_value = '8f44d9bb-527c-4d1d-b259-ee9ac62e11b6'
        mock_manifest.get_assay_process.return_value = {
            'content': {
                'insdc_experiment': {
                    'insdc_experiment_accession': 'ERX123456'
                }
            },
            'uuid': {'uuid': '21aa0e1a-a31b-42ae-a82b-5773c481e36b'}
        }
        files = load_json(f'{self.expected_dir}/files.json')
        mock_manifest.get_files.return_value = files
        return mock_manifest

    def test_convert_sequencing_run_data_to_xml_tree(self):
        # given
        run_data = load_json(f'{self.expected_dir}/sequencing_run_data.json')

        # when
        tree = self.run_converter.convert_sequencing_run_data_to_xml_tree(run_data)

        # then
        actual_file = f'{self.actual_dir}/actual.xml'
        write_xml(tree, actual_file)
        actual = load_xml(actual_file)

        expected_file = f'{self.expected_dir}/sample_run.xml'
        expected = load_xml(expected_file)

        self.assertEqual(actual, expected)

    def test_load_md5_file(self):
        # when
        md5 = self.run_converter.load_md5_file(f'{self.expected_dir}/md5.txt')

        # then
        expected = load_json(f'{self.expected_dir}/md5.json')
        self.assertEqual(md5, expected)
