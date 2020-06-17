import json
import logging
import os
from typing import Iterator, List

import requests
from ingest.utils.s2s_token_client import S2STokenClient
from ingest.utils.token_manager import TokenManager
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

        if os.environ.get('INGEST_API_GCP'):
            token_client = S2STokenClient()
            token_client.setup_from_env_var('INGEST_API_GCP')
            self.token_manager = TokenManager(token_client)
        else:
            self.token_manager = False

    def set_token(self, token):
        self.token = token
        self.headers['Authorization'] = self.token
        self.logger.debug(f'Token set!')

        return self.headers

    def get_headers(self):
        # refresh token
        if self.token_manager:
            self.set_token(f'Bearer {self.token_manager.get_token()}')
            self.logger.debug(f'Token refreshed!')

        return self.headers

    def get_related_entity(self, entity, relation, related_entity_type) -> Iterator['dict']:
        related_entity_uri = self._get_link(entity, relation)
        related_entities = self._get_all(related_entity_uri, related_entity_type)
        return related_entities

    def get_related_entity_count(self, entity, relation, entity_type) -> int:
        if relation in entity["_links"]:
            entity_uri = entity["_links"][relation]["href"]
            result = self.get(entity_uri)
            page = result.get('page')
            if page:
                return page.get('totalElements')
            return len(result["_embedded"][entity_type])

    def get_submission_by_id(self, submission_id):
        get_submission_url = self.url + '/submissionEnvelopes/' + submission_id

        response = self.session.get(get_submission_url, headers=self.get_headers())

        submission = None

        if response.ok:
            submission = response.json()

        return submission

    def get_concrete_entity_type(self, entity):
        content = entity.get('content')
        schema_url = content.get('describedBy')
        response = self.session.get(schema_url, headers=self.get_headers())
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
            response = self.session.get(entity_url, headers=self.get_headers())
            entity_json = self._handle_response(response)
            self._cache_entity(entity_url, entity_json)
        return entity_json

    def patch_entity_by_id(self, entity_type, entity_id, entity_patch):
        entity_url = f'{self.url}/{entity_type}/{entity_id}'
        patch = json.dumps(entity_patch)
        response = self.session.patch(entity_url, patch, headers=self.get_headers())
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

    def get_manifests_from_project(self, project_uuid, bundle_type="PRIMARY"):
        entity_url = f'{self.url}/projects/search/findBundleManifestsByProjectUuidAndBundleType' + \
                     f'?projectUuid={project_uuid}&bundleType={bundle_type}'
        return self._get_all(entity_url, 'bundleManifests')

    def get_manifest_ids_from_project(self, project_uuid):
        manifests = self.get_manifests_from_project(project_uuid, "PRIMARY")
        return self.get_manifest_ids(manifests)

    def get_manifest_ids_from_submission(self, submission_uuid):
        manifests = self.get_manifests_from_submission(submission_uuid)
        return self.get_manifest_ids(manifests)

    def get_manifest_ids(self, manifests: List['dict']):
        return [self.get_entity_id(manifest, 'bundleManifests') for manifest in manifests]

    def get_manifests_from_submission(self, submission_uuid):
        entity_url = f'{self.url}/bundleManifests/search/findByEnvelopeUuid?uuid={submission_uuid}'
        return self._get_all(entity_url, 'bundleManifests')

    def get_entity_id(self, entity, entity_type):
        entity_base = f'{self.url}/{entity_type}/'
        entity_uri = self._get_link(entity, 'self')
        entity_id = str.replace(entity_uri, entity_base, '').strip('/')
        return entity_id

    def entity_info_from_url(self, url):
        location = str.replace(url, self.url, '').strip('/')
        entity_type = location.split('/')[0]
        entity_id = location.split('/')[1]
        return entity_type, entity_id

    @staticmethod
    def _handle_response(response):
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _get_link(entity, link_name):
        link = entity['_links'][link_name]
        return link['href'].rsplit("{")[0] if link else ''

    def _get_all(self, url, entity_type):
        r = self.session.get(url, headers=self.get_headers())
        r.raise_for_status()
        if "_embedded" in r.json():
            for entity in r.json()["_embedded"][entity_type]:
                yield entity
            while "next" in r.json()["_links"]:
                r = self.session.get(r.json()["_links"]["next"]["href"], headers=self.get_headers())
                for entity in r.json()["_embedded"][entity_type]:
                    yield entity

    def create_archive_submission(self, archive_submission):
        url = f'{self.url}/archiveSubmissions/'
        return self.post(url, archive_submission)

    def create_archive_entity(self, archive_submission_url, archive_entity):
        url = f'{archive_submission_url}/entities'
        return self.post(url, archive_entity)

    def get_archive_submission_by_dsp_uuid(self, dsp_uuid):
        url = f'{self.url}/archiveSubmissions/search/findByDspUuid?dspUuid={dsp_uuid}'
        return self.get(url)

    def get_archive_entity_by_dsp_uuid(self, dsp_uuid):
        url = f'{self.url}/archiveEntities/search/findByDspUuid?dspUuid={dsp_uuid}'
        return self.get(url)

    def get_archive_entity_by_alias(self, alias):
        url = f'{self.url}/archiveEntities/search/findByAlias?alias={alias}'
        return self.get(url)

    def get(self, url, **kwargs):
        r = self.session.get(url, headers=self.headers, **kwargs)
        r.raise_for_status()
        return r.json()

    def post(self, url, content):
        r = self.session.post(url, json=content, headers=self.headers)
        r.raise_for_status()
        return r.json()

    def patch(self, url, patch):
        r = self.session.patch(url, json=patch, headers=self.headers)
        r.raise_for_status()
        return r.json()
