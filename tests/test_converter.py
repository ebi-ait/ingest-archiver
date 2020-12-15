import json
import unittest
from copy import deepcopy
from random import randint

from mock import MagicMock, patch

import config
from archiver.dsp.converter.ena_experiment import EnaExperimentConverter
from archiver.dsp.converter.ena_run import EnaRunConverter
from archiver.dsp.converter.biostudy import BiostudyConverter
from archiver.dsp.converter.ena_study import EnaStudyConverter
from archiver.dsp.converter.biosample import BiosampleConverter


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
        self.ontology_api.expand_curie = MagicMock(return_value='http://purl.obolibrary.org/obo/UO_0000015')

    def test_convert_sample(self):
        # given:
        biomaterial = self.hca_data.get('biomaterial')
        with open(config.JSON_DIR + 'dsp/sample.json', encoding=config.ENCODING) as data_file:
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
        converter = BiosampleConverter(ontology_api=self.ontology_api)
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
            'project': {
                'releaseDate': None
            }
        })

        # then:
        self.assertEqual(with_release_date, converted_with_release_date)
        self.assertEqual(no_release_date, converted_no_release_date)

    @patch('api.ontology.OntologyAPI.expand_curie')
    def test_convert_sequencing_experiment(self, expand_curie):
        # given:
        expand_curie.return_value = 'http://purl.obolibrary.org/obo/UO_0000015'
        # and:
        process = dict(self.hca_data.get('process'))
        lib_prep_protocol = dict(self.hca_data.get('library_preparation_protocol'))
        input_biomaterial = dict(self.hca_data.get('input_biomaterial'))
        sequencing_protocol = dict(self.hca_data.get('sequencing_protocol'))

        # and:
        test_alias = 'alias'
        process['uuid']['uuid'] = test_alias
        sequencing_protocol['uuid']['uuid'] = 'seqprotocol' + test_alias
        lib_prep_protocol['uuid']['uuid'] = 'libprepprotol' + test_alias

        # and:
        with open(config.JSON_DIR + 'dsp/sequencing_experiment.json', encoding=config.ENCODING) as data_file:
            expected_json = json.loads(data_file.read())
        expected_json['attributes'][
            'HCA Input Biomaterial UUID'] = [
            {'value': input_biomaterial['uuid']['uuid']}]
        expected_json['attributes'][
            'HCA Library Preparation Protocol UUID'] = [
            {'value': lib_prep_protocol['uuid']['uuid']}]
        expected_json['attributes'][
            'HCA Sequencing Protocol UUID'] = [
            {'value': sequencing_protocol['uuid']['uuid']}]
        expected_json['attributes'][
            'HCA Process UUID'] = [{'value': process['uuid']['uuid']}]

        # when:
        converter = EnaExperimentConverter(ontology_api=self.ontology_api)
        actual_json = converter.convert({
            'input_biomaterial': input_biomaterial,
            'process': process,
            'sequencing_protocol': sequencing_protocol,
            'library_preparation_protocol': lib_prep_protocol
        })
        self.assertEqual(expected_json, actual_json)

        # then:
        instrument_model_text = "illumina hiseq 2500"
        ena_instrument_model_text = "Illumina HiSeq 2500"
        sequencing_protocol['content']['instrument_manufacturer_model']["text"] = instrument_model_text
        expected_json['attributes']['instrument_model'][0]['value'] = ena_instrument_model_text
        actual_json = converter.convert({
            'input_biomaterial': input_biomaterial,
            'process': process,
            'sequencing_protocol': sequencing_protocol,
            'library_preparation_protocol': lib_prep_protocol
        })
        self.assertEqual(expected_json, actual_json, 'Must match ENA enum values for instrument_model')

    def test_convert_sequencing_run(self):
        self.ontology_api.expand_curie = MagicMock(return_value='http://purl.obolibrary.org/obo/UO_0000015')
        lib_prep_protocol = dict(self.hca_data.get('library_preparation_protocol'))
        sequencing_protocol = dict(self.hca_data.get('sequencing_protocol'))
        file = dict(self.hca_data.get('sequencing_file'))

        uuid = 'process' + str(randint(0, 1000))
        test_alias = f'sequencingRun_{uuid}'
        with open(config.JSON_DIR + 'dsp/sequencing_run.json', encoding=config.ENCODING) as data_file:
            expected_json = json.loads(data_file.read())

        process = dict(self.hca_data.get('process'))
        process['uuid']['uuid'] = uuid

        converter = EnaRunConverter(ontology_api=self.ontology_api)
        actual_json = converter.convert({
            'library_preparation_protocol': lib_prep_protocol,
            'sequencing_protocol': sequencing_protocol,
            'process': process,
            'files': [file]
        })

        self.assertEqual(expected_json, actual_json)

    def test_convert_sequencing_run_10x(self):
        self.ontology_api.expand_curie = MagicMock(return_value='http://purl.obolibrary.org/obo/UO_0000015')
        with open(f'{config.JSON_DIR}hca/library_preparation_protocol_10x.json', encoding=config.ENCODING) as data_file:
            lib_prep_protocol = json.loads(data_file.read())

        uuid = f'process{str(randint(0, 1000))}'
        process = dict(self.hca_data.get('process'))
        process['uuid']['uuid'] = uuid
        sequencing_protocol = dict(self.hca_data.get('sequencing_protocol'))
        file = dict(self.hca_data.get('sequencing_file'))
        hca_data = {
            'library_preparation_protocol': lib_prep_protocol,
            'sequencing_protocol': sequencing_protocol,
            'process': process,
            'files': [file],
            'manifest_id': 'dummy_manifest_id'
        }

        test_alias = f'sequencingRun_{uuid}'
        with open(config.JSON_DIR + 'dsp/sequencing_run_10x.json', encoding=config.ENCODING) as data_file:
            expected_json = json.loads(data_file.read())

        converter = EnaRunConverter(ontology_api=self.ontology_api)
        actual_json = converter.convert(hca_data)
        self.assertEqual(expected_json, actual_json)

    @patch('api.ontology.OntologyAPI.expand_curie')
    def test_convert_project(self, expand_curie):
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
        converter = BiostudyConverter()
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
        converter = EnaStudyConverter()
        actual_json = converter.convert({
            'project': hca_data
        })

        # then:
        self.assertEqual(expected_json, actual_json)
