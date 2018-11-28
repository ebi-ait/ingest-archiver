import unittest
import json
import config

from archiver import util


class TestUtil(unittest.TestCase):
    def test_is_10x_true(self):
        with open(config.JSON_DIR + 'hca/library_preparation_protocol_10x.json', encoding=config.ENCODING) as data_file:
            lib_prep_protocol = json.loads(data_file.read())

        is10x = util.is_10x(lib_prep_protocol)
        self.assertTrue(is10x)

    def test_is_10x_false(self):
        with open(config.JSON_DIR + 'hca/library_preparation_protocol.json', encoding=config.ENCODING) as data_file:
            lib_prep_protocol = json.loads(data_file.read())

        is10x = util.is_10x(lib_prep_protocol)
        self.assertFalse(is10x)
