import json
import unittest
from os.path import dirname
from unittest.mock import MagicMock

from submission_broker.submission.entity import Entity

from submitter.biosamples_submitter_service import BioSamplesSubmitterService


class BioSamplesSubmitterServiceTest(unittest.TestCase):

    def setUp(self) -> None:
        self.archive_client = MagicMock()
        self.env = 'dev'
        self.submitter_service = BioSamplesSubmitterService(self.archive_client, self.env)

        with open(dirname(__file__) + '/../../resources/biomaterial_entity.json') as file:
            self.biomaterial: Entity = Entity('biomaterials', 0, attributes=json.load(file))

    def test_update_sample_with_biostudies_accession(self):
        biostudies_accession = 'BST-123'

        self.submitter_service.update_sample_with_biostudies_accession(self.biomaterial, biostudies_accession)

        actual_external_references = self.biomaterial.attributes.get('externalReferences')

        self.assertEqual(len(actual_external_references), 1)
        self.assertIn(biostudies_accession, actual_external_references[0].get('url'))


if __name__ == '__main__':
    unittest.main()
