import logging
import config
import requests
from urllib.parse import quote


# iri: "http://purl.obolibrary.org/obo/UBERON_0000948"
# curie: "obo:UBERON_0000948"
# label: "heart"
# short_form: "UBERON_0000948"
# obo_id: "UBERON:0000948"
class OntologyAPI:
    def __init__(self, url=None):
        self.url = url if url else config.ONTOLOGY_API_URL
        self.logger = logging.getLogger(__name__)
        self.logger.info(f'Using {self.url}')

    def search(self, term, exact=True, obsolete=False, group=True, query_fields=None):
        if not term:
            raise Error(f'Search term must be supplied.')

        exact = 'true' if exact else 'false'
        obsolete = 'true' if obsolete else 'false'
        group = 'true' if group else 'false'

        params = f'q={quote(term)}&exact={exact}&obsoletes={obsolete}&groupField={group}'
        if query_fields:
            params += f'&queryFields={query_fields}'
        response = get_json(f'{self.url}/api/search?{params}').get('response')
        doc = None
        if response and response.get('numFound') and response.get('docs'):
            docs = response.get('docs')
            doc = docs[0] if docs else None
        return doc

    def iri_from_obo_id(self, obo_id):
        term = self.find_by_id_defining(obo_id)
        if term and 'iri' in term:
            return term['iri']

    def find_by_id_defining(self, obo_id):
        obo_id = obo_id.replace(':', '_')
        query_url = f'{self.url}/api/terms/?short_form={obo_id}'
        all_terms = get_all(query_url, 'terms')
        all_terms = [term for term in all_terms if term.get('is_defining_ontology')]
        if all_terms:
            return all_terms[0]

    def is_equal_or_descendant(self, reference_obo_id, test_obo_id):
        if reference_obo_id == test_obo_id:
            return True
        return self.is_descendant(reference_obo_id, test_obo_id)

    def is_descendant(self, reference_obo_id, test_obo_id):
        reference_doc = self.search(reference_obo_id, exact=True)
        if not reference_doc:
            raise Error(f'Could not find {reference_obo_id}')
        ontology_name = reference_doc.get('ontology_name')
        iri = reference_doc.get('iri')
        for descendant in self.get_descendants(ontology_name, iri):
            if test_obo_id == descendant.get('obo_id', ''):
                return True
        return False

    def get_descendants(self, ontology_name, iri):
        safe_iri = quote(quote(iri, safe=''))
        query_url = f'{self.url}/api/ontologies/{ontology_name}/terms/{safe_iri}/descendants'
        return get_all(query_url, 'terms')


def get_all(query_url, result_type):
    results = []
    while query_url:
        response: dict = get_json(query_url)
        results.extend(response.get('_embedded', {}).get(result_type, []))
        query_url = response.get('_links', {}).get('next', {}).get('href', None)
    return results


def get_json(query_url):
    response = requests.get(query_url)
    response.raise_for_status()
    return response.json()


class Error(Exception):
    """Base-class for all exceptions raised by this module."""


__api__ = OntologyAPI()
