import config

class OntologyAPI:
    def __init__(self, url=None):
        self.url = url if url else config.ONTOLOGY_API_URL
        self.logger.info(f'Using {self.url}')

    def expandCurie(self, term):
