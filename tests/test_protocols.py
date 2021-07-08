import json
from unittest import TestCase
from unittest.mock import Mock
from utils import protocols
from api.ontology import OntologyAPI
from utils.protocols import ONTOLOGY_3PRIME_PARENT, ONTOLOGY_5PRIME_PARENT


class TestProtocols(TestCase):
    def setUp(self) -> None:
        self.ontology_api = Mock()

    def test_is_10x__when_equal_3prime_parent__returns_true(self):
        # given
        lib_prep_protocol = {
            'content': {
                'library_construction_method': {
                    'ontology': ONTOLOGY_3PRIME_PARENT
                }
            }
        }

        # when
        is10x = protocols.is_10x(OntologyAPI(), lib_prep_protocol)

        # then
        self.assertTrue(is10x)

    def test_is_10x__when_equal_5prime_parent__returns_true(self):
        # given
        lib_prep_protocol = {
            'content': {
                'library_construction_method': {
                    'ontology': ONTOLOGY_5PRIME_PARENT
                }
            }
        }

        # when
        is10x = protocols.is_10x(self.ontology_api, lib_prep_protocol)

        # then
        self.assertTrue(is10x)

    def test_is_10x__when_equal_citeseq__returns_true(self):
        # given
        lib_prep_protocol = {
            'content': {
                'library_construction_method': {
                    'ontology': 'EFO:0009294'
                }
            }
        }

        # when
        is10x = protocols.is_10x(self.ontology_api, lib_prep_protocol)

        # then
        self.assertTrue(is10x)

    def test_is_10x__when_not_descendant__returns_false(self):
        lib_prep_protocol = {
            "content": {
                "library_construction_method": {
                    "ontology": "EFO:0000000",
                }
            }
        }

        self.ontology_api.is_equal_or_descendant = Mock(return_value=False)
        is10x = protocols.is_10x(self.ontology_api, lib_prep_protocol)
        self.assertFalse(is10x)

    def test_map_bam_schema__when_equals_citeseq__returns_10xV2(self):
        # given
        lib_prep_protocol = {
            "content": {
                "library_construction_method": {
                    "ontology": "EFO:0009294",
                }
            }
        }

        # when
        bam_schema = protocols.map_10x_bam_schema(self.ontology_api, lib_prep_protocol)

        # then
        self.assertEqual(bam_schema, '10xV2')

    def test_map_bam_schema__when_not_leaf_term__returns_none(self):
        # given
        lib_prep_protocol = {
            "content": {
                "library_construction_method": {
                    "ontology": "EFO:0000000",
                }
            }
        }

        self.ontology_api.get_descendants = Mock(return_value=['descendant'])
        self.ontology_api.search = Mock(return_value={'ontology_name': 'name', 'iri': 'iri', 'label': "10x 5' v2"})

        # when
        bam_schema = protocols.map_10x_bam_schema(self.ontology_api, lib_prep_protocol)

        # then
        self.assertEqual(bam_schema, None)

    def test_map_bam_schema__when_leaf_term__returns_correct_bam_schema(self):
        # given
        lib_prep_protocol = {
            "content": {
                "library_construction_method": {
                    "ontology": "EFO:0009294",
                }
            }
        }

        self.ontology_api.is_leaf_term = Mock(return_value=True)
        self.ontology_api.version_10x_by_label = Mock(return_value='V2')

        # when
        bam_schema = protocols.map_10x_bam_schema(self.ontology_api, lib_prep_protocol)

        # then
        self.assertEqual(bam_schema, '10xV2')

    def test_version_10x_by_label__given_label__return_version(self):
        # given
        lib_prep_protocol = {
            "content": {
                "library_construction_method": {
                    "ontology": "EFO:0009294",
                }
            }
        }

        self.ontology_api.search = Mock(return_value={'label': "10x 5' v2"})

        # when
        bam_schema = protocols.version_10x_by_label(self.ontology_api, lib_prep_protocol)

        # then
        self.assertEqual(bam_schema, 'V2')

    def test_version_10x_by_label__given_label__return_version(self):
        # given
        lib_prep_protocol = {
            "content": {
                "library_construction_method": {
                    "ontology": "EFO:0009294",
                }
            }
        }

        self.ontology_api.search = Mock(return_value={'label': "10x 3' v3"})

        # when
        bam_schema = protocols.version_10x_by_label(self.ontology_api, lib_prep_protocol)

        # then
        self.assertEqual(bam_schema, 'V3')
