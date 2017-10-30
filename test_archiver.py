import unittest
import archiver
import json


class FirstTest(unittest.TestCase):
    def test_given_hca_sample_extract_attributes(self):
        with open('flatten-hca.json', encoding='utf-8') as data_file:
            flattened_hca = json.loads(data_file.read())

        attributes = archiver.extract_attributes(flattened_hca)

        expected_json = [{
            "name": "is_living",
            "value": "yes",
            "terms": []
        }, {
            "name": "ncbi_taxon",
            "value": 9606,
            "terms": []
        }, {
            "name": "release",
            "value": "2017-10-17T23:30:04.489Z",
            "terms": []
        }]
        self.assertEqual(attributes, expected_json)

    def test_given_hca_sample_json_file_return_usi_json(self):
        with open('usi-sample.json', encoding='utf-8') as data_file:
            expected_json = json.loads(data_file.read())
        actual_json = archiver.convert_to_usi('hca-sample.json')
        print(expected_json)
        print(actual_json)
        self.assertEqual(actual_json, expected_json)
