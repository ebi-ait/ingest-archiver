import re

from json_converter.json_mapper import JsonMapper
from submission_broker.submission.submission import Submission, Entity, HandleCollision

from hca.accession_mapper import AccessionMapper


class HcaSubmission(Submission):
    _accession_spec = {
        'BioSamples': {
            'biomaterials': AccessionMapper(mapping=['content.biomaterial_core.biosamples_accession'],
                                            accession_type='string')
        },
        'BioStudies': {
            'projects': AccessionMapper(mapping=['content.biostudies_accessions'],
                                        accession_type='array')
        },
        'ENA': {
            'projects': AccessionMapper(mapping=['content.insdc_project_accessions'],
                                        accession_type='array'),
            'study': AccessionMapper(mapping=['content.insdc_study_accessions'],
                                     accession_type='array'),
            'biomaterials': AccessionMapper(mapping=['content.biomaterial_core.insdc_sample_accession'],
                                            accession_type='string'),
            'processes': AccessionMapper(mapping=['content.insdc_experiment'],
                                         accession_type='string'),
            'files': AccessionMapper(mapping=['content.insdc_run_accessions'],
                                     accession_type='array')
        }
    }

    def __init__(self, collider: HandleCollision = None):
        self.__uuid_map = {}
        self.__regex = re.compile(r'/(?P<entity_type>\w+)/(?P<entity_id>\w+)$')
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

    def add_accessions_to_attributes(self, entity: Entity, archive_type: str, entity_type: str):
        accession = entity.get_accession(archive_type)

        if accession:
            accession_mappers_by_archive = self._accession_spec.get(archive_type)
            accession_mapper = accession_mappers_by_archive.get(entity_type)
            accession_location = accession_mapper.mapping
            accession_type = accession_mapper.type
            if accession_location:
                self.__set_accession_by_attribute_location(accession, accession_location, accession_type,
                                                           entity)

    def __set_accession_by_attribute_location(self, accession, accession_location, accession_type,
                                              entity):
        location_list = accession_location[0]
        attributes = entity.attributes
        locations = location_list.split('.')
        while len(locations) > 1:
            location = locations.pop(0)
            attributes.setdefault(location, {})
            attributes = attributes[location]
        if accession_type == 'array':
            attributes[locations[0]] = [accession]
        else:
            attributes[locations[0]] = accession

    def __get_entity_key(self, entity_attributes: dict) -> [str, str]:
        entity_uri = HcaSubmission.get_link(entity_attributes, 'self')
        match = self.__regex.search(entity_uri)
        entity_type = match.group('entity_type')
        entity_id = match.group('entity_id')
        return entity_type, entity_id

    def _get_accessions_from_attributes(self, entity: Entity):
        entity_type = entity.identifier.entity_type
        for service, accession_map_by_entity_type in self._accession_spec.items():
            accession_mapper = accession_map_by_entity_type.get(entity_type)
            if accession_mapper:
                accession_mappers_by_archive = self._accession_spec.get(service)
                accession_mapper = accession_mappers_by_archive.get(entity_type)
                accession_location = accession_mapper.mapping
                accession = JsonMapper(entity.attributes).map({entity_type: accession_location}).get(entity_type)
                if accession:
                    entity.add_accession(service, accession)

    @staticmethod
    def get_uuid(entity_attributes: dict) -> str:
        return entity_attributes.get('uuid', {}).get('uuid', '')

    @staticmethod
    def get_link(entity_attributes: dict, link_name: str) -> str:
        link = entity_attributes['_links'][link_name]
        return link['href'].rsplit("{")[0] if link else ''

    @staticmethod
    def get_all_accession_spec():
        return HcaSubmission._accession_spec

    @staticmethod
    def get_accession_spec_by_archive(archive_name: str):
        return HcaSubmission._accession_spec.get(archive_name)
