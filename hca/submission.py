import re

from submission_broker.submission.submission import Submission, HandleCollision
from submission_broker.submission.entity import Entity


class HcaSubmission(Submission):
    def __init__(self, collider: HandleCollision = None):
        self.__uuid_map = {}
        self.regex = re.compile(r'/(?P<entity_type>\w+)/(?P<entity_id>\w+)$')
        super().__init__(collider)

    def map_ingest_entity(self, entity_attributes: dict) -> Entity:
        entity_type, entity_id = self.get_entity_key(entity_attributes)
        entity_uuid = self.__get_uuid(entity_attributes)
        if not entity_uuid and entity_type == 'bundleManifests':
            entity_uuid = entity_id
        self.__uuid_map.setdefault(entity_type, {})[entity_uuid] = entity_id
        return super().map(entity_type, entity_id, entity_attributes)

    def get_entity_from_uuid(self, entity_type: str, entity_uuid: str) -> Entity:
        if self.ingest_uuid_cached(entity_type, entity_uuid):
            return super().get_entity(entity_type, self.__uuid_map[entity_type][entity_uuid])

    def ingest_uuid_cached(self, entity_type: str, entity_uuid: str) -> bool:
        return entity_uuid in self.__uuid_map.get(entity_type, {})

    def ingest_entity_cached(self, entity_attributes) -> bool:
        entity_type, entity_id = self.get_entity_key(entity_attributes)
        if super().get_entity(entity_type, entity_id):
            return True
        return False

    def get_entity_key(self, entity_attributes: dict) -> [str, str]:
        entity_uri = HcaSubmission.__get_link(entity_attributes, 'self')
        match = self.regex.search(entity_uri)
        entity_type = match.group('entity_type')
        entity_id = match.group('entity_id')
        return entity_type, entity_id

    @staticmethod
    def __get_uuid(entity_attributes: dict) -> str:
        return entity_attributes.get('uuid', {}).get('uuid', '')

    @staticmethod
    def __get_link(entity_attributes: dict, link_name: str) -> str:
        link = entity_attributes['_links'][link_name]
        return link['href'].rsplit("{")[0] if link else ''
