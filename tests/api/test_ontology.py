from unittest import TestCase
from unittest.mock import patch

from api.ontology import OntologyAPI


class OntologyAPITest(TestCase):
    def setUp(self):
        self.ontology_api = OntologyAPI()

    @patch('api.ontology.get_all')
    def test_find_by_id_defining(self, mock_get_all):
        # given
        defining_ontology = {'is_defining_ontology': True}
        not_defining_ontology = {'is_defining_ontology': False}
        mock_get_all.return_value = [defining_ontology, not_defining_ontology]

        # when
        actual = self.ontology_api.find_by_id_defining('obo-id')

        # then
        self.assertEqual(actual, defining_ontology)

    @patch('api.ontology.get_all')
    def test_find_by_id_defining__no_result(self, mock_get_all):
        # given
        ontology_1 = {'is_defining_ontology': False}
        ontology_2 = {'is_defining_ontology': False}
        mock_get_all.return_value = [ontology_1, ontology_2]

        # when
        actual = self.ontology_api.find_by_id_defining('obo-id')

        # then
        self.assertEqual(actual, None)