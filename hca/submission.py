import re

from submission_broker.submission.submission import Submission, HandleCollision
from submission_broker.submission.entity import Entity


class HcaSubmission(Submission):
    def __init__(self, collider: HandleCollision = None):
        self.uuid_map = {}
        super().__init__(collider)

    def map_ingest_entity(self, entity_type: str, entity_attributes: dict) -> Entity:
        entity_id = self.__get_entity_id(entity_type, entity_attributes)
        entity_uuid = self.__get_uuid(entity_attributes)
        if not entity_uuid and entity_type == 'bundleManifests':
            entity_uuid = entity_id
        self.uuid_map.setdefault(entity_type, {})[entity_uuid] = entity_id
        return super().map(entity_type, entity_id, entity_attributes)

    def get_entity_from_uuid(self, entity_type: str, uuid: str) -> Entity:
        if uuid in self.uuid_map.get(entity_type, {}):
            return super().get_entity(entity_type, self.uuid_map[entity_type][uuid])
    
    @staticmethod
    def __get_uuid(entity: dict) -> str:
        return entity.get('uuid', {}).get('uuid', '')
    
    @staticmethod
    def __get_entity_id(entity_type: str, entity_attributes: dict) -> str:
        entity_uri = HcaSubmission.__get_link(entity_attributes, 'self')
        id_match = re.search(f'/{entity_type}/' + r'(.*)$', entity_uri)
        entity_id = id_match.group(1) if id_match else ''
        return entity_id
    
    @staticmethod
    def __get_link(entity: dict, link_name: str) -> str:
        link = entity['_links'][link_name]
        return link['href'].rsplit("{")[0] if link else ''
