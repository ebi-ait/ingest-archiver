import unittest
import json
import config

from random import randint

from archiver.converter import Converter, SampleConverter, AssayConverter


class TestConverter(unittest.TestCase):
    def test_convert_sample(self):
        converter = SampleConverter()

        with open(config.JSON_DIR + 'hca/biomaterial.json', encoding=config.ENCODING) as data_file:
            hca_data = json.loads(data_file.read())

        with open(config.JSON_DIR + 'usi/sample.json', encoding=config.ENCODING) as data_file:
            expected_json = json.loads(data_file.read())

        test_alias = 'hca' + str(randint(0, 1000))

        hca_data['uuid']['uuid'] = test_alias
        expected_json['alias'] = test_alias

        actual_json = converter.convert(hca_data)

        self.assertEqual(actual_json, expected_json)

    def test_convert_assay(self):
        converter = AssayConverter()

        with open(config.JSON_DIR + 'hca/sequencing_process.json', encoding=config.ENCODING) as data_file:
            process = json.loads(data_file.read())

        with open(config.JSON_DIR + 'hca/library_preparation_protocol.json', encoding=config.ENCODING) as data_file:
            lib_prep_protocol = json.loads(data_file.read())

        with open(config.JSON_DIR + 'hca/cell_suspension.json', encoding=config.ENCODING) as data_file:
            input_biomaterial = json.loads(data_file.read())

        with open(config.JSON_DIR + 'hca/sequencing_protocol.json', encoding=config.ENCODING) as data_file:
            sequencing_protocol = json.loads(data_file.read())

        with open(config.JSON_DIR + 'usi/sequencing_experiment.json', encoding=config.ENCODING) as data_file:
            expected_json = json.loads(data_file.read())

        test_alias = str(randint(0, 1000))

        process['uuid']['uuid'] = 'process' + test_alias
        sequencing_protocol['uuid']['uuid'] = 'seqprotocol' + test_alias
        lib_prep_protocol['uuid']['uuid'] = 'libprepprotol' + test_alias

        hca_data = {
            'process': process,
            'sequencing_protocol': sequencing_protocol,
            'library_preparation_protocol': lib_prep_protocol
        }

        expected_json['alias'] = 'process' + test_alias

        actual_json = converter.convert(hca_data)

        self.assertEqual(actual_json, expected_json)
