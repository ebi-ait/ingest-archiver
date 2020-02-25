import logging

import requests
from requests import adapters
from urllib3.util import retry

import config


class IngestAPI:
    def __init__(self, url=None):
        self.logger = logging.getLogger(__name__)
        self.headers = {
            'Content-type': 'application/json',
        }
        self.url = url if url else config.INGEST_API_URL
        self.url = self.url.rstrip('/')
        self.logger.info(f'Using {self.url}')
        self.entity_cache = {}
        self.cache_enabled = True

        retry_policy = retry.Retry(
            total=100,  # seems that this has a default value of 10,
            # setting this to a very high number so that it'll respect the status retry count
            status=17,  # status is the no. of retries if response is in status_forcelist,
            # this count will retry for ~20mins with back off timeout within
            read=10,
            status_forcelist=[500, 502, 503, 504],
            backoff_factor=0.6)

        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(max_retries=retry_policy)
        self.session.mount('https://', adapter)

    def get_related_entity(self, entity, relation, related_entity_type):
        related_entity_uri = self._get_link(entity, relation)
        related_entities = list(self._get_all(related_entity_uri, related_entity_type))
        return related_entities

    def get_submission_by_id(self, submission_id):
        get_submission_url = self.url + '/submissionEnvelopes/' + submission_id

        response = self.session.get(get_submission_url, headers=self.headers)

        submission = None

        if response.ok:
            submission = response.json()

        return submission

    def get_concrete_entity_type(self, entity):
        content = entity.get('content')
        schema_url = content.get('describedBy')
        response = self.session.get(schema_url, headers=self.headers)
        schema = self._handle_response(response)

        return schema.get('name')

    def get_entity_by_uuid(self, entity_type, uuid):
        entity_url = f'{self.url}/{entity_type}/search/findByUuid?uuid={uuid}'
        return self.get_entity(entity_url)

    def get_entity_by_id(self, entity_type, entity_id):
        entity_url = f'{self.url}/{entity_type}/{entity_id}'
        return self.get_entity(entity_url)

    def get_entity(self, entity_url):
        entity_json = self._get_cached_entity(entity_url)
        if not entity_json:
            response = self.session.get(entity_url, headers=self.headers)
            entity_json = self._handle_response(response)
            self._cache_entity(entity_url, entity_json)
        return entity_json

    def _get_cached_entity(self, url):
        if self.cache_enabled and self.entity_cache.get(url):
            return self.entity_cache.get(url)

    def _cache_entity(self, url, entity_json):
        if self.cache_enabled and not self.entity_cache.get(url):
            self.entity_cache[url] = entity_json

    def get_submission_by_uuid(self, submission_uuid):
        return self.get_entity_by_uuid('submissionEnvelopes', submission_uuid)

    def get_biomaterial_by_uuid(self, biomaterial_uuid):
        return self.get_entity_by_uuid('biomaterials', biomaterial_uuid)

    def get_project_by_uuid(self, project_uuid):
        return self.get_entity_by_uuid('projects', project_uuid)

    def get_file_by_uuid(self, file_uuid):
        return self.get_entity_by_uuid('files', file_uuid)

    def get_manifest_by_id(self, manifest_id):
        return self.get_entity_by_id('bundleManifests', manifest_id)

    def get_manifest_ids(self, project_uuid):
        project = self.get_project_by_uuid(project_uuid)
        manifests = self.get_related_entity(project, "bundleManifests", "bundleManifests")
        manifest_ids = []
        for manifest in manifests:
            manifest_ids.append(self.get_entity_id(manifest, 'bundleManifests'))
        return manifest_ids

    def get_entity_id(self, entity, entity_type):
        entity_base = f'{self.url}/{entity_type}/'
        entity_uri = self._get_link(entity, 'self')
        entity_id = str.strip(entity_uri.replace(entity_base, ''), '/')
        return entity_id

    @staticmethod
    def _handle_response(response):
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _get_link(entity, link_name):
        link = entity['_links'][link_name]
        return link['href'].rsplit("{")[0] if link else ''

    def _get_all(self, url, entity_type):
        r = self.session.get(url, headers=self.headers)
        r.raise_for_status()
        if "_embedded" in r.json():
            for entity in r.json()["_embedded"][entity_type]:
                yield entity
            while "next" in r.json()["_links"]:
                r = self.session.get(r.json()["_links"]["next"]["href"], headers=self.headers)
                for entity in r.json()["_embedded"][entity_type]:
                    yield entity
