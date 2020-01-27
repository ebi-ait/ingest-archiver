import logging

import config
import requests

from urllib.parse import quote


class OntologyAPI:
    def __init__(self, url=None):
        self.url = url if url else config.ONTOLOGY_API_URL
        self.logger = logging.getLogger(__name__)
        self.logger.info(f'Using {self.url}')

    def expand_curie(self, term):
        iri = self.search(term)
        if iri:
            return iri

        iri = self.search(term, obsolete=True)
        if iri:
            return iri

        raise Error(f'Could not retrieve IRI for {term}')

    def search(self, term, exact=True, obsolete=False, group=True, query_fields='obo_id'):
        exact = 'true' if exact else 'false'
        obsolete = 'true' if obsolete else 'false'
        group = 'true' if group else 'false'

        params = f'q={quote(term)}&exact={exact}&obsoletes={obsolete}&groupField={group}&queryFields={query_fields}'
        query_url = f'{self.url}/api/search?{params}'
        r = requests.get(query_url)
        r.raise_for_status()
        body = r.json()
        response = body.get('response')

        iri = None
        if response and response.get('numFound') and response.get('docs'):
            docs = response.get('docs')
            iri = docs[0].get('iri') if docs else None
        return iri


class Error(Exception):
    """Base-class for all exceptions raised by this module."""
