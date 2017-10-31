import unittest
import json

from archiver.converter import Converter

JSON_DIR = 'tests/json/'
ENCODING = 'utf-8'


class TestConverter(unittest.TestCase):
    def test_convert_sample_given_hca_sample_json_return_usi_json(self):
        converter = Converter()

        with open(JSON_DIR + 'hca-sample.json', encoding=ENCODING) as data_file:
            hca_data = json.loads(data_file.read())

        with open(JSON_DIR + 'usi-sample.json', encoding=ENCODING) as data_file:
            expected_json = json.loads(data_file.read())

        actual_json = converter.convert_sample(hca_data)

        self.assertEqual(actual_json, expected_json)
