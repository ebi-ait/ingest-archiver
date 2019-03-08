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
        term = quote(term)
        params = f'q={term}&exact=true&groupField=true&queryFields=obo_id'
        query_url = f'{self.url}/api/search?{params}'

        r = requests.get(query_url)
        r.raise_for_status()
        body = r.json()
        response = body.get('response')

        if response and response.get('numFound') and response.get('docs'):
            docs = response.get('docs')
            iri = docs[0].get('iri') if docs else None

            if not iri:
                raise Error(f'Could not retrieve IRI for {term}')

        return iri


class Error(Exception):
    """Base-class for all exceptions raised by this module."""
