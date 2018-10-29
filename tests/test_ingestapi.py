import unittest
import config
import json

from archiver.ingestapi import IngestAPI
from mock import MagicMock


class TestIngestAPI(unittest.TestCase):
    def setUp(self):
        self.ingest_api = IngestAPI()
        pass

    def test_get_biomaterials_in_bundle(self):
        with open(config.JSON_DIR + 'hca/bundle_manifest.json', encoding=config.ENCODING) as data_file:
            bundle_manifest = json.loads(data_file.read())
        with open(config.JSON_DIR + 'hca/biomaterial.json', encoding=config.ENCODING) as data_file:
            biomaterial = json.loads(data_file.read())

        self.ingest_api.get_bundle_manifest = MagicMock(return_value=bundle_manifest)
        self.ingest_api.get_biomaterial_by_uuid = MagicMock(return_value=biomaterial)

        biomaterials = list(self.ingest_api.get_biomaterials_in_bundle('dummy_bundle_uuid'))

        self.assertEqual(3, len(biomaterials))
