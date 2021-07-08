import json
from unittest import TestCase

import config
from utils import protocols
from api.ontology import quote, get_json, get_all


class MockOntologyAPI:
    children_10x = ['EFO:0009897', 'EFO:0009310', 'EFO:0009898']
    children_10xV1 = ['EFO:0009901']
    children_10xV2 = ['EFO:0009899', 'EFO:0009900', 'EFO:0010713', 'EFO:0010715', 'EFO:0010714']
    children_10xV3 = ['EFO:0009922', 'EFO:0009921']

    def __init__(self):
        self.children_10x.extend(self.children_10xV1)
        self.children_10x.extend(self.children_10xV2)
        self.children_10x.extend(self.children_10xV3)

    def is_equal_or_descendant(self, root_obo_id, child_obo_id):
        if root_obo_id == child_obo_id:
            return True
        elif root_obo_id == 'EFO:0008995':  # 10x
            return child_obo_id in self.children_10x
        elif root_obo_id == 'EFO:0009897':  # 10xV1
            return child_obo_id in self.children_10xV1
        elif root_obo_id == 'EFO:0009310':  # 10xV2
            return child_obo_id in self.children_10xV2
        elif root_obo_id == 'EFO:0009898':  # 10xV3
            return child_obo_id in self.children_10xV3
        return False

    def search(self, term, exact=True, obsolete=False, group=True, query_fields=None):
        if not term:
            return False

        exact = 'true' if exact else 'false'
        obsolete = 'true' if obsolete else 'false'
        group = 'true' if group else 'false'

        params = f'q={quote(term)}&exact={exact}&obsoletes={obsolete}&groupField={group}'
        if query_fields:
            params += f'&queryFields={query_fields}'
        response = get_json(f'https://ontology.staging.archive.data.humancellatlas.org/api/search?{params}').get('response')
        doc = None
        if response and response.get('numFound') and response.get('docs'):
            docs = response.get('docs')
            doc = docs[0] if docs else None
        return doc

    def get_descendants(self, ontology_name, iri):
        safe_iri = quote(quote(iri, safe=''))
        query_url = f'https://ontology.staging.archive.data.humancellatlas.org/api/ontologies/{ontology_name}/terms/{safe_iri}/descendants'
        return get_all(query_url, 'terms')


class TestProtocols(TestCase):
    def setUp(self) -> None:
        self.ontology_api = MockOntologyAPI()

    def test_is_10x_true(self):
        with open(config.JSON_DIR + 'hca/library_preparation_protocol_10x.json', encoding=config.ENCODING) as data_file:
            lib_prep_protocol = json.loads(data_file.read())

        is10x = protocols.is_10x(self.ontology_api, lib_prep_protocol)
        self.assertTrue(is10x)

    def test_is_10x_citeSeq(self):
        lib_prep_protocol = {
            "content": {
                "library_construction_method": {
                    "text": "CITE-seq",
                    "ontology": "EFO:0009294",
                    "ontology_label": "CITE-seq"
                }
            }
        }

        is10x = protocols.is_10x(self.ontology_api, lib_prep_protocol)
        self.assertTrue(is10x)

    def test_is_10x_false(self):
        with open(config.JSON_DIR + 'hca/library_preparation_protocol.json', encoding=config.ENCODING) as data_file:
            lib_prep_protocol = json.loads(data_file.read())

        is10x = protocols.is_10x(self.ontology_api, lib_prep_protocol)
        self.assertFalse(is10x)

    def test_map_bam_schema_v2(self):
        with open(config.JSON_DIR + 'hca/library_preparation_protocol_10x.json', encoding=config.ENCODING) as data_file:
            lib_prep_protocol = json.loads(data_file.read())

        bam_schema = protocols.map_10x_bam_schema(self.ontology_api, lib_prep_protocol)
        self.assertEqual(bam_schema, '10xV2')

    def test_map_bam_schema_v2_citeSeq(self):
        lib_prep_protocol = {
            "content": {
                "library_construction_method": {
                    "text": "CITE-seq",
                    "ontology": "EFO:0009294",
                    "ontology_label": "CITE-seq"
                }
            }
        }

        bam_schema = protocols.map_10x_bam_schema(self.ontology_api, lib_prep_protocol)
        self.assertEqual(bam_schema, '10xV2')

    def test_map_bam_schema_v3(self):
        with open(config.JSON_DIR + 'hca/library_preparation_protocol_10xV3.json',
                  encoding=config.ENCODING) as data_file:
            lib_prep_protocol = json.loads(data_file.read())

        bam_schema = protocols.map_10x_bam_schema(self.ontology_api, lib_prep_protocol)
        self.assertEqual(bam_schema, '10xV3')
