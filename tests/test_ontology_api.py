import unittest
from api.ontology import OntologyAPI


class TestOntologyAPI(unittest.TestCase):
    def setUp(self):
        self.ontology_api = OntologyAPI()

    def test_expand_curie(self):
        iri = self.ontology_api.expand_curie('UO:0000015')
        self.assertTrue(iri)
