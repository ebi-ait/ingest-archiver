import unittest
import json
import config

from random import randint

from archiver.converter import Converter, SampleConverter, SequencingExperimentConverter, SequencingRunConverter, \
    StudyConverter, ProjectConverter


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

        input = {
            'biomaterial': hca_data
        }

        actual_json = converter.convert(input)

        self.assertEqual(expected_json, actual_json )

    def test_convert_sequencing_experiment(self):
        converter = SequencingExperimentConverter()

        with open(config.JSON_DIR + 'hca/process.json', encoding=config.ENCODING) as data_file:
            process = json.loads(data_file.read())

        with open(config.JSON_DIR + 'hca/library_preparation_protocol.json', encoding=config.ENCODING) as data_file:
            lib_prep_protocol = json.loads(data_file.read())

        with open(config.JSON_DIR + 'hca/cell_suspension.json', encoding=config.ENCODING) as data_file:
            input_biomaterial = json.loads(data_file.read())

        with open(config.JSON_DIR + 'hca/sequencing_protocol.json', encoding=config.ENCODING) as data_file:
            sequencing_protocol = json.loads(data_file.read())

        with open(config.JSON_DIR + 'usi/sequencing_experiment.json', encoding=config.ENCODING) as data_file:
            expected_json = json.loads(data_file.read())

        test_alias = 'process' + str(randint(0, 1000))
        process['uuid']['uuid'] = test_alias
        sequencing_protocol['uuid']['uuid'] = 'seqprotocol' + test_alias
        lib_prep_protocol['uuid']['uuid'] = 'libprepprotol' + test_alias

        hca_data = {
            'process': process,
            'sequencing_protocol': sequencing_protocol,
            'library_preparation_protocol': lib_prep_protocol
        }

        expected_json['alias'] = 'sequencingExperiment_' + test_alias

        actual_json = converter.convert(hca_data)

        self.assertEqual(expected_json, actual_json)

    def test_convert_sequencing_run(self):
        converter = SequencingRunConverter()

        with open(config.JSON_DIR + 'hca/process.json', encoding=config.ENCODING) as data_file:
            process = json.loads(data_file.read())

        with open(config.JSON_DIR + 'hca/sequencing_protocol.json', encoding=config.ENCODING) as data_file:
            sequencing_protocol = json.loads(data_file.read())

        with open(config.JSON_DIR + 'hca/sequencing_file.json', encoding=config.ENCODING) as data_file:
            file = json.loads(data_file.read())

        with open(config.JSON_DIR + 'usi/sequencing_run.json', encoding=config.ENCODING) as data_file:
            expected_json = json.loads(data_file.read())

        test_alias = 'process' + str(randint(0, 1000))

        process['uuid']['uuid'] = test_alias

        hca_data = {
            'sequencing_protocol': sequencing_protocol,
            'process': process,
            'files': [file]
        }

        expected_json['alias'] = 'sequencingRun_' + test_alias

        actual_json = converter.convert(hca_data)

        self.assertEqual(expected_json, actual_json)

    def test_convert_project(self):
        converter = ProjectConverter()

        with open(config.JSON_DIR + 'hca/project.json', encoding=config.ENCODING) as data_file:
            hca_data = json.loads(data_file.read())

        with open(config.JSON_DIR + 'usi/project.json', encoding=config.ENCODING) as data_file:
            expected_json = json.loads(data_file.read())

        test_alias = 'hca' + str(randint(0, 1000))

        hca_data['uuid']['uuid'] = test_alias
        expected_json['alias'] = 'project_' + test_alias

        input = {
            'project': hca_data
        }

        actual_json = converter.convert(input)

        self.assertEqual(expected_json, actual_json)

    def test_convert_study(self):
        self.maxDiff = None
        converter = StudyConverter()

        with open(config.JSON_DIR + 'hca/project.json', encoding=config.ENCODING) as data_file:
            hca_data = json.loads(data_file.read())

        with open(config.JSON_DIR + 'usi/study.json', encoding=config.ENCODING) as data_file:
            expected_json = json.loads(data_file.read())

        test_alias = 'hca' + str(randint(0, 1000))

        hca_data['uuid']['uuid'] = test_alias
        expected_json['alias'] = 'study_' + test_alias

        input = {
            'project': hca_data
        }

        actual_json = converter.convert(input)

        self.assertEqual(expected_json, actual_json)