import logging

import config
import requests
import json

from urllib.parse import quote


class OntologyAPI:
    def __init__(self, url=None):
        self.url = url if url else config.ONTOLOGY_API_URL
        self.logger = logging.getLogger(__name__)
        self.logger.info(f'Using {self.url}')

    def expand_curie(self, term):
        iri = self.search_for_iri(term)
        if iri:
            return iri

        iri = self.search_for_iri(term, obsolete=True)
        if iri:
            return iri

        raise Error(f'Could not retrieve IRI for {term}')

    def search_for_iri(self, term, exact=True, obsolete=False, group=True, query_fields=None):
        doc = self.search(term,exact,obsolete,group,query_fields)
        return doc.get('iri') if doc else None

    def search(self, term, exact=True, obsolete=False, group=True, query_fields=None):
        if not term:
            raise Error(f'Search term must be supplied.')

        exact = 'true' if exact else 'false'
        obsolete = 'true' if obsolete else 'false'
        group = 'true' if group else 'false'

        params = f'q={quote(term)}&exact={exact}&obsoletes={obsolete}&groupField={group}'
        if query_fields:
            params += f'&queryFields={query_fields}'
        response = self.get_json(f'{self.url}/api/search?{params}').get('response')
        doc = None
        if response and response.get('numFound') and response.get('docs'):
            docs = response.get('docs')
            doc = docs[0] if docs else None
        return doc

    def is_child_of(self, root_obo_id, child_obo_id):
        root_doc = self.search(root_obo_id, exact=True)
        if not root_doc:
            raise Error(f'Could not find {root_obo_id}')
        root_ontology_name = root_doc.get('ontology_name')
        root_iri = root_doc.get('iri')
        for descendant in self.get_descendants(root_ontology_name, root_iri):
            descendant_obo_id = descendant.get('obo_id', '')
            if child_obo_id == descendant_obo_id:
                return True
        return False

    def get_descendants(self, ontology_name, iri):
        query_url = f'{self.url}/api/ontologies/{ontology_name}/terms/{quote(iri)}/descendants'
        return self.get_all(query_url, 'terms')

    def get_all(self, query_url, result_type):
        results = []
        while query_url:
            response: dict = self.get_json(query_url)
            results.extend(response.get('_embedded',{}).get(result_type,[]))
            query_url = response.get('_links', {}).get('next', {}).get('href', None)
        return results

    def get_json(self, query_url):
        response = requests.get(query_url)
        response.raise_for_status()
        return response.json()


class Error(Exception):
    """Base-class for all exceptions raised by this module."""


__api__ = OntologyAPI()
