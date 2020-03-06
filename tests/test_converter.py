import unittest
import json

from mock import MagicMock

import config

from random import randint

from archiver import project
from archiver.converter import Converter, SampleConverter, SequencingExperimentConverter, SequencingRunConverter, \
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
        self.ontology_api.expand_curie = MagicMock(return_value='http://purl.obolibrary.org/obo/UO_0000015')

    def test_convert_sample(self):
        biomaterial = self.hca_data.get('biomaterial')

        with open(config.JSON_DIR + 'dsp/sample.json', encoding=config.ENCODING) as data_file:
            expected_json = json.loads(data_file.read())

        test_alias = 'hca' + str(randint(0, 1000))

        biomaterial['uuid']['uuid'] = test_alias
        expected_json['alias'] = test_alias
        expected_json['attributes']['HCA Biomaterial UUID'] = [{'value': test_alias}]

        input = {
            'biomaterial': biomaterial
        }

        converter = SampleConverter(ontology_api=self.ontology_api)
        converter.ingest_api = self.ingest_api
        actual_json = converter.convert(input)

        self.assertEqual(expected_json, actual_json)

    def test_convert_sequencing_experiment(self):
        self.ontology_api.expand_curie = MagicMock(return_value='http://purl.obolibrary.org/obo/UO_0000015')
        process = dict(self.hca_data.get('process'))
        lib_prep_protocol = dict(self.hca_data.get('library_preparation_protocol'))
        input_biomaterial = dict(self.hca_data.get('input_biomaterial'))
        sequencing_protocol = dict(self.hca_data.get('sequencing_protocol'))

        test_alias = 'alias'
        process['uuid']['uuid'] = test_alias
        sequencing_protocol['uuid']['uuid'] = 'seqprotocol' + test_alias
        lib_prep_protocol['uuid']['uuid'] = 'libprepprotol' + test_alias

        with open(config.JSON_DIR + 'dsp/sequencing_experiment.json', encoding=config.ENCODING) as data_file:
            expected_json = json.loads(data_file.read())
        expected_json['alias'] = 'sequencingExperiment_' + test_alias

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

        hca_data = {
            'input_biomaterial': input_biomaterial,
            'process': process,
            'sequencing_protocol': sequencing_protocol,
            'library_preparation_protocol': lib_prep_protocol
        }

        converter = SequencingExperimentConverter(ontology_api=self.ontology_api)
        actual_json = converter.convert(hca_data)
        self.assertEqual(expected_json, actual_json)

        instrument_model_text = "Illumina Hiseq 2500"
        ena_instrument_model_text = "Illumina HiSeq 2500"
        sequencing_protocol['content']['instrument_manufacturer_model']["text"] = instrument_model_text
        expected_json['attributes']['instrument_model'][0]['value'] = ena_instrument_model_text
        actual_json = converter.convert(hca_data)
        self.assertEqual(expected_json, actual_json, 'Must match ENA enum values for instrument_model')

        instrument_model_text = "HiSeq X Five"
        ena_instrument_model_text = "HiSeq X Five"
        sequencing_protocol['content']['instrument_manufacturer_model']["text"] = instrument_model_text
        expected_json['attributes']['instrument_model'][0]['value'] = ena_instrument_model_text
        actual_json = converter.convert(hca_data)
        self.assertEqual(expected_json, actual_json, 'Must match ENA enum values for instrument_model')

        instrument_model_text = "hiseq X Five"
        ena_instrument_model_text = "HiSeq X Five"
        sequencing_protocol['content']['instrument_manufacturer_model']["text"] = instrument_model_text
        expected_json['attributes']['instrument_model'][0]['value'] = ena_instrument_model_text
        actual_json = converter.convert(hca_data)
        self.assertEqual(expected_json, actual_json, 'Must match ENA enum values for instrument_model')

        instrument_model_text = "fsfa X Five"
        ena_instrument_model_text = "unspecified"
        sequencing_protocol['content']['instrument_manufacturer_model']["text"] = instrument_model_text
        expected_json['attributes']['instrument_model'][0]['value'] = ena_instrument_model_text
        expected_json['attributes']['platform_type'][0]['value'] = 'unspecified'
        actual_json = converter.convert(hca_data)
        self.assertEqual(expected_json, actual_json, 'Must match ENA enum values for instrument_model')

        instrument_model_text = "Illumina Hiseq X 10"
        ena_instrument_model_text = "HiSeq X Ten"
        sequencing_protocol['content']['instrument_manufacturer_model']["text"] = instrument_model_text
        expected_json['attributes']['instrument_model'][0]['value'] = ena_instrument_model_text
        expected_json['attributes']['platform_type'][0]['value'] = 'ILLUMINA'
        actual_json = converter.convert(hca_data)
        self.assertEqual(expected_json, actual_json, 'Must match ENA enum values for instrument_model')

    def test_convert_sequencing_run(self):
        self.ontology_api.expand_curie = MagicMock(return_value='http://purl.obolibrary.org/obo/UO_0000015')
        process = dict(self.hca_data.get('process'))
        lib_prep_protocol = dict(self.hca_data.get('library_preparation_protocol'))
        sequencing_protocol = dict(self.hca_data.get('sequencing_protocol'))
        file = dict(self.hca_data.get('sequencing_file'))

        with open(config.JSON_DIR + 'dsp/sequencing_run.json', encoding=config.ENCODING) as data_file:
            expected_json = json.loads(data_file.read())

        test_alias = 'process' + str(randint(0, 1000))

        process['uuid']['uuid'] = test_alias

        hca_data = {
            'library_preparation_protocol': lib_prep_protocol,
            'sequencing_protocol': sequencing_protocol,
            'process': process,
            'files': [file]
        }

        expected_json['alias'] = 'sequencingRun_' + test_alias

        expected_json['attributes'][
            'HCA Library Preparation Protocol UUID'] = [{'value': lib_prep_protocol['uuid']['uuid']}]
        expected_json['attributes'][
            'HCA Sequencing Protocol UUID'] = [{'value': sequencing_protocol['uuid']['uuid']}]
        expected_json['attributes'][
            'HCA Process UUID'] = [{'value': process['uuid']['uuid']}]
        expected_json['attributes'][
            "HCA Files UUID's"] = [
            {'value': ', '.join([e["uuid"]["uuid"] for e in [file]])}]

        converter = SequencingRunConverter(ontology_api=self.ontology_api)
        actual_json = converter.convert(hca_data)

        self.assertEqual(expected_json, actual_json)

    def test_convert_sequencing_run_10x(self):
        self.ontology_api.expand_curie = MagicMock(return_value='http://purl.obolibrary.org/obo/UO_0000015')

        process = dict(self.hca_data.get('process'))
        sequencing_protocol = dict(self.hca_data.get('sequencing_protocol'))
        file = dict(self.hca_data.get('sequencing_file'))

        with open(config.JSON_DIR + 'hca/library_preparation_protocol_10x.json', encoding=config.ENCODING) as data_file:
            lib_prep_protocol = json.loads(data_file.read())

        with open(config.JSON_DIR + 'dsp/sequencing_run_10x.json', encoding=config.ENCODING) as data_file:
            expected_json = json.loads(data_file.read())

        test_alias = 'process' + str(randint(0, 1000))

        process['uuid']['uuid'] = test_alias

        hca_data = {
            'library_preparation_protocol': lib_prep_protocol,
            'sequencing_protocol': sequencing_protocol,
            'process': process,
            'files': [file],
            'manifest_id': 'dummy_manifest_id'
        }

        expected_json['alias'] = 'sequencingRun_' + test_alias
        expected_json['attributes'][
            'HCA Library Preparation Protocol UUID'] = [
            {'value': lib_prep_protocol['uuid']['uuid']}]
        expected_json['attributes'][
            'HCA Sequencing Protocol UUID'] = [
            {'value': sequencing_protocol['uuid']['uuid']}]
        expected_json['attributes'][
            'HCA Process UUID'] = [{'value': process['uuid']['uuid']}]
        expected_json['attributes'][
            "HCA Files UUID's"] = [
            {'value': ', '.join([e["uuid"]["uuid"] for e in [file]])}]

        converter = SequencingRunConverter(ontology_api=self.ontology_api)
        actual_json = converter.convert(hca_data)

        self.assertEqual(expected_json, actual_json)

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
