import re

from json_converter.json_mapper import JsonMapper
from submission_broker.submission.submission import Submission, Entity, HandleCollision


class HcaSubmission(Submission):
    def __init__(self, collider: HandleCollision = None):
        self.__uuid_map = {}
        self.__regex = re.compile(r'/(?P<entity_type>\w+)/(?P<entity_id>\w+)$')
        self._accession_spec = {
            'BioSamples': ['content.biomaterial_core.biosamples_accession'],
            'BioStudies': ['content.biostudies_accessions']
        }
        super().__init__(collider)

    def map_ingest_entity(self, entity_attributes: dict) -> Entity:
        entity_type, entity_id = self.__get_entity_key(entity_attributes)
        entity_uuid = self.get_uuid(entity_attributes)
        if not entity_uuid and entity_type == 'bundleManifests':
            entity_uuid = entity_id
        existing_entity = super().get_entity(entity_type, entity_id)
        if existing_entity:
            return existing_entity
        self.__uuid_map.setdefault(entity_type, {})[entity_uuid] = entity_id
        entity = super().map(entity_type, entity_id, entity_attributes)
        self._get_accessions_from_attributes(entity)
        return entity

    def get_entity_by_uuid(self, entity_type: str, entity_uuid: str) -> Entity:
        if self.contains_entity_by_uuid(entity_type, entity_uuid):
            return super().get_entity(entity_type, self.__uuid_map[entity_type][entity_uuid])

    def contains_entity_by_uuid(self, entity_type: str, entity_uuid: str) -> bool:
        return entity_uuid in self.__uuid_map.get(entity_type, {})

    def contains_entity(self, entity_attributes: dict) -> bool:
        entity_type, entity_id = self.__get_entity_key(entity_attributes)
        if super().get_entity(entity_type, entity_id):
            return True
        return False

    def add_accessions_to_attributes(self, entity: Entity):
        for service, mapping_list in self._accession_spec.items():
            if service == 'BioSamples':
                accession = entity.get_accession(service)
            else:
                accession = [entity.get_accession(service)]

            if accession:
                location_list = mapping_list[0]
                attributes = entity.attributes
                locations = location_list.split('.')
                while len(locations) > 1:
                    location = locations.pop(0)
                    attributes.setdefault(location, {})
                    attributes = attributes[location]
                attributes[locations[0]] = accession

    def __get_entity_key(self, entity_attributes: dict) -> [str, str]:
        entity_uri = HcaSubmission.get_link(entity_attributes, 'self')
        match = self.__regex.search(entity_uri)
        entity_type = match.group('entity_type')
        entity_id = match.group('entity_id')
        return entity_type, entity_id

    def _get_accessions_from_attributes(self, entity: Entity):
        accessions = JsonMapper(entity.attributes).map(self._accession_spec)
        for service, accession in accessions.items():
            entity.add_accession(service, accession)

    @staticmethod
    def get_uuid(entity_attributes: dict) -> str:
        return entity_attributes.get('uuid', {}).get('uuid', '')

    @staticmethod
    def get_link(entity_attributes: dict, link_name: str) -> str:
        link = entity_attributes['_links'][link_name]
        return link['href'].rsplit("{")[0] if link else ''
