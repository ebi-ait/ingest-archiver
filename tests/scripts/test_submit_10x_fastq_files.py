import json
import xmltodict

from unittest import TestCase
from unittest.mock import MagicMock, patch, Mock

from scripts.submit_10x_fastq_files import SequencingRunDataConverter


def load_xml(filename) -> dict:
    with open(filename) as xml_file:
        xml_dict = xmltodict.parse(xml_file.read())
        xml_file.close()
    return xml_dict


def write_xml(tree, filename):
    tree.write(filename, encoding="UTF-8", xml_declaration=True)


def load_json(filename):
    with open(filename) as json_file:
        data = json.load(json_file)
    return data


class TestSequencingRunDataConverter(TestCase):
    def setUp(self) -> None:
        self.ingest_api = MagicMock()
        self.run_xml_converter = SequencingRunDataConverter(self.ingest_api)

    def test_prepare_sequencing_run_data(self):
        # given
        mock_manifest = self._create_mock_manifest()
        self.run_xml_converter.get_manifest = Mock(return_value=mock_manifest)

        # when
        manifest_id = '60f2a4a6d5d575160aafb78f'
        run_data = self.run_xml_converter.prepare_sequencing_run_data(manifest_id)

        expected_run_data = load_json('sequencing_run_data.json')

        # then
        self.assertEqual(run_data, expected_run_data)

    def _create_mock_manifest(self):
        mock_manifest = Mock()
        mock_manifest.get_submission_uuid.return_value = '8f44d9bb-527c-4d1d-b259-ee9ac62e11b6'
        mock_manifest.get_assay_process.return_value = {'uuid': {'uuid': '21aa0e1a-a31b-42ae-a82b-5773c481e36b'}}
        files = load_json('files.json')
        mock_manifest.get_files.return_value = files
        return mock_manifest

    def test_convert_sequencing_run_data_to_xml_tree(self):
        # given
        run_data = load_json('sequencing_run_data.json')

        # when
        tree = self.run_xml_converter.convert_sequencing_run_data_to_xml_tree(run_data)

        # then
        actual_file = 'actual.xml'
        write_xml(tree, actual_file)
        actual = load_xml(actual_file)

        expected_file = 'sample_run.xml'
        expected = load_xml(expected_file)

        self.assertEqual(actual, expected)
