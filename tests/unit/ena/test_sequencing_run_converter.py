import json
import os
import tempfile
from unittest import TestCase
from unittest.mock import MagicMock, Mock

from ena import sequencing_run_converter
from ena.sequencing_run_converter import SequencingRunConverter
from ena.util import load_json, load_xml_dict, write_xml


# for converting load_xml_dict output from xmltodict.parse to be unordered dict for assert comparisons
def to_unordered_dict(ordered_dict: dict):
    return json.loads(json.dumps(ordered_dict))


class TestSequencingRunDataConverter(TestCase):
    def setUp(self) -> None:
        self.ingest_api = MagicMock()
        self.run_converter = SequencingRunConverter(self.ingest_api)
        self.temp_dir = tempfile.TemporaryDirectory()
        self.actual_dir = self.temp_dir.name
        self.expected_dir = os.path.dirname(__file__) + '/data'

        files = load_json(f'{self.expected_dir}/files.json')
        mock_manifest = self._create_mock_manifest(files)
        self.run_converter.get_manifest = Mock(return_value=mock_manifest)

    def test_prepare_sequencing_runs__with_ftp_parent_dir(self):
        # given
        md5_file = f'{self.expected_dir}/md5.txt'
        manifest_id = '60f2a4a6d5d575160aafb78f'

        # when
        runs = self.run_converter.prepare_sequencing_runs(manifest_id, md5_file,
                                                                  '8f44d9bb-527c-4d1d-b259-ee9ac62e11b6')

        expected_run_data = load_json(f'{self.expected_dir}/sequencing_run_data__with_ftp_dir.json')

        # then
        self.assertEqual(runs, [expected_run_data])

    def test_prepare_sequencing_runs(self):
        # given
        md5_file = f'{self.expected_dir}/md5.txt'
        manifest_id = '60f2a4a6d5d575160aafb78f'

        # when
        runs = self.run_converter.prepare_sequencing_runs(manifest_id, md5_file)

        expected_run_data = load_json(f'{self.expected_dir}/sequencing_run_data__no_dir.json')

        # then
        self.assertEqual(runs, [expected_run_data])

    def test_prepare_sequencing_runs__experiment_with_multiple_runs(self):
        # given
        md5_file = f'{self.expected_dir}/md5_files_in_multiple_lanes.txt'
        manifest_id = '60f2a4a6d5d575160aafb78f'
        files = load_json(f'{self.expected_dir}/files_in_multiple_lanes.json')
        mock_manifest = self._create_mock_manifest(files)
        self.run_converter.get_manifest = Mock(return_value=mock_manifest)

        # when
        runs = self.run_converter.prepare_sequencing_runs(manifest_id, md5_file)

        expected_runs = load_json(f'{self.expected_dir}/sequencing_runs_in_multiple_lanes.json')

        # then
        self.assertEqual(runs, expected_runs)

    def test_prepare_sequencing_runs__add_with_no_experiment_acession(self):
        # given
        md5_file = f'{self.expected_dir}/md5.txt'
        manifest_id = '60f2a4a6d5d575160aafb78f'
        files = load_json(f'{self.expected_dir}/files.json')
        mock_manifest = self._create_mock_manifest(files)
        mock_manifest.get_assay_process.return_value = {
            'content': {},
            'uuid': {'uuid': '21aa0e1a-a31b-42ae-a82b-5773c481e36b'}
        }
        self.run_converter.get_manifest = Mock(return_value=mock_manifest)

        # when
        with self.assertRaises(sequencing_run_converter.Error) as e:
            run_data = self.run_converter.prepare_sequencing_runs(manifest_id, md5_file)
            self.assertFalse(run_data)

    def test_prepare_sequencing_runs__modify_with_run_accession(self):
        # given
        md5_file = f'{self.expected_dir}/md5.txt'
        manifest_id = '60f2a4a6d5d575160aafb78f'
        files = load_json(f'{self.expected_dir}/files_with_run_accession.json')
        mock_manifest = self._create_mock_manifest(files)
        self.run_converter.get_manifest = Mock(return_value=mock_manifest)

        # when
        runs = self.run_converter.prepare_sequencing_runs(manifest_id, md5_file, action='MODIFY')

        expected_run_data = load_json(f'{self.expected_dir}/sequencing_run_data__with_run_accession.json')

        # then
        self.assertEqual(runs, [expected_run_data])

    def test_prepare_sequencing_runs__modify_with_no_run_accession__raises_error(self):
        # given
        md5_file = f'{self.expected_dir}/md5.txt'
        manifest_id = '60f2a4a6d5d575160aafb78f'
        files = load_json(f'{self.expected_dir}/files.json')
        mock_manifest = self._create_mock_manifest(files)
        self.run_converter.get_manifest = Mock(return_value=mock_manifest)

        # when
        with self.assertRaises(sequencing_run_converter.Error) as e:
            runs = self.run_converter.prepare_sequencing_runs(manifest_id, md5_file, action='MODIFY')
            self.assertFalse(runs)

    def test_prepare_sequencing_runs__add_with_run_accession__raises_error(self):
        # given
        md5_file = f'{self.expected_dir}/md5.txt'
        manifest_id = '60f2a4a6d5d575160aafb78f'
        files = load_json(f'{self.expected_dir}/files_with_run_accession.json')
        mock_manifest = self._create_mock_manifest(files)
        self.run_converter.get_manifest = Mock(return_value=mock_manifest)

        # when
        with self.assertRaises(sequencing_run_converter.Error) as e:
            runs = self.run_converter.prepare_sequencing_runs(manifest_id, md5_file, action='ADD')
            self.assertFalse(runs)

    def _create_mock_manifest(self, files):
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
        mock_manifest.get_files.return_value = files
        return mock_manifest

    def test_convert_sequencing_run_data_to_xml_tree(self):
        # given
        run_data = load_json(f'{self.expected_dir}/sequencing_run_data__with_ftp_dir.json')

        # when
        tree = self.run_converter.convert_sequencing_run_data_to_xml_tree([run_data])

        # then
        actual_file = f'{self.actual_dir}/actual.xml'
        write_xml(tree, actual_file)
        actual = load_xml_dict(actual_file)

        expected_file = f'{self.expected_dir}/sample_add_run.xml'
        expected = load_xml_dict(expected_file)

        self.assertEqual(to_unordered_dict(actual), to_unordered_dict(expected))

    def test_convert_sequencing_run_data_to_xml_tree__multiple_runs(self):
        # given
        run_data = load_json(f'{self.expected_dir}/sequencing_run_data__with_ftp_dir.json')
        run_data_2 = load_json(f'{self.expected_dir}/sequencing_run_data__with_ftp_dir_2.json')

        # when
        tree = self.run_converter.convert_sequencing_run_data_to_xml_tree([run_data, run_data_2])

        # then
        actual_file = f'{self.actual_dir}/actual.xml'
        write_xml(tree, actual_file)
        actual = load_xml_dict(actual_file)

        expected_file = f'{self.expected_dir}/sample_add_multiple_runs.xml'
        expected = load_xml_dict(expected_file)

        self.assertEqual(to_unordered_dict(actual), to_unordered_dict(expected))

    def test_load_md5_file(self):
        # when
        md5 = self.run_converter.load_md5_file(f'{self.expected_dir}/md5.txt')

        # then
        expected = load_json(f'{self.expected_dir}/md5.json')
        self.assertEqual(md5, expected)

