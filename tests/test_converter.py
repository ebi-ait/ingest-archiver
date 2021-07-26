import json
import unittest
from copy import deepcopy
from random import randint

from mock import MagicMock, patch

import config
from archiver.converter import SampleConverter, SequencingExperimentConverter, SequencingRunConverter, \
    StudyConverter, ProjectConverter


class TestConverter(unittest.TestCase):
    def setUp(self):
        with open(config.JSON_DIR + 'hca/process.json', encoding=config.ENCODING) as data_file:
            process = json.loads(data_file.read())

        with open(config.JSON_DIR + 'hca/library_preparation_protocol.json', encoding=config.ENCODING) as data_file:
            lib_prep_protocol = json.loads(data_file.read())

        with open(config.JSON_DIR + 'hca/cell_suspension.json', encoding=config.ENCODING) as data_file:
            input_biomaterial = json.loads(data_file.read())

        with open(config.JSON_DIR + 'hca/sequencing_protocol.json', encoding=config.ENCODING) as data_file:
            sequencing_protocol = json.loads(data_file.read())

        with open(config.JSON_DIR + 'hca/biomaterial.json', encoding=config.ENCODING) as data_file:
            biomaterial = json.loads(data_file.read())

        with open(config.JSON_DIR + 'hca/sequencing_file.json', encoding=config.ENCODING) as data_file:
            file = json.loads(data_file.read())

        self.hca_data = {
            'process': process,
            'library_preparation_protocol': lib_prep_protocol,
            'input_biomaterial': input_biomaterial,
            'sequencing_protocol': sequencing_protocol,
            'biomaterial': biomaterial,
            'sequencing_file': file
        }

        self.maxDiff = None
        self.ingest_api = MagicMock()
        self.ingest_api.url = 'ingest_url'
        self.ingest_api.get_concrete_entity_type = MagicMock(return_value='donor_organism')
        self.ontology_api = MagicMock()

    def test_convert_sample(self):
        # given:
        biomaterial = self.hca_data.get('biomaterial')
        with open(config.JSON_DIR + 'dsp/sample_run.json', encoding=config.ENCODING) as data_file:
            no_release_date = json.loads(data_file.read())

        # and:
        test_alias = 'hca' + str(randint(0, 1000))
        biomaterial['uuid']['uuid'] = test_alias
        no_release_date['alias'] = test_alias
        no_release_date['attributes']['HCA Biomaterial UUID'] = [{'value': test_alias}]

        # and:
        with_release_date = deepcopy(no_release_date)
        with_release_date['releaseDate'] = '2018-10-11'

        # and:
        converter = SampleConverter(ontology_api=self.ontology_api)
        converter.ingest_api = self.ingest_api

        # when:
        converted_with_release_date = converter.convert({
            'biomaterial': biomaterial,
            'project': {
                'releaseDate': '2018-10-11T14:33:22.111Z'
            }
        })

        # and:
        converted_no_release_date = converter.convert({
            'biomaterial': biomaterial,
            'project': {}
        })

        # then:
        self.assertEqual(with_release_date, converted_with_release_date)
        self.assertEqual(no_release_date, converted_no_release_date)

    def test_convert_project(self):
        # given: read from files
        with open(config.JSON_DIR + 'hca/project.json', encoding=config.ENCODING) as data_file:
            hca_data = json.loads(data_file.read())
        with open(config.JSON_DIR + 'dsp/project.json', encoding=config.ENCODING) as data_file:
            expected_json = json.loads(data_file.read())

        # and:
        test_alias = 'hca' + str(randint(0, 1000))
        hca_data['uuid']['uuid'] = test_alias
        expected_json['alias'] = 'project_' + test_alias
        expected_json['attributes']['HCA Project UUID'] = [{'value': test_alias}]

        # when:
        converter = ProjectConverter(ontology_api=self.ontology_api)
        actual_json = converter.convert({
            'project': hca_data
        })

        # then:
        self.assertEqual(expected_json, actual_json)

    def test_convert_study(self):
        # given:
        with open(config.JSON_DIR + 'hca/project.json', encoding=config.ENCODING) as data_file:
            hca_data = json.loads(data_file.read())
        with open(config.JSON_DIR + 'dsp/study.json', encoding=config.ENCODING) as data_file:
            expected_json = json.loads(data_file.read())

        # and:
        test_alias = 'hca' + str(randint(0, 1000))
        hca_data['uuid']['uuid'] = test_alias
        expected_json['alias'] = 'study_' + test_alias
        expected_json['attributes']['HCA Project UUID'] = [{'value': test_alias}]

        # when:
        converter = StudyConverter(ontology_api=self.ontology_api)
        actual_json = converter.convert({
            'project': hca_data
        })

        # then:
        self.assertEqual(expected_json, actual_json)
