from typing import List, Iterator

from .dsp.entity import IngestDspEntity


class ArchiveEntityMap:
    def __init__(self):
        self.entities_dict_type = {}

    def add_entities(self, entities):
        for entity in entities:
            self.add_entity(entity)

    def add_entity(self, entity: IngestDspEntity):
        if not self.entities_dict_type.get(entity.archive_entity_type):
            self.entities_dict_type[entity.archive_entity_type] = {}
        self.entities_dict_type[entity.archive_entity_type][entity.id] = entity

    def get_entity(self, entity_type, archive_entity_id):
        if self.entities_dict_type.get(entity_type):
            return self.entities_dict_type[entity_type].get(archive_entity_id)
        return None

    def get_converted_entities(self):
        entities = []
        for entities_dict in self.entities_dict_type.values():
            for entity in entities_dict.values():
                if entity.conversion and not entity.errors:
                    entities.append(entity)
        return entities

    def get_conversion_summary(self):
        summary = {}
        for entities_dict in self.entities_dict_type.values():
            for entity in entities_dict.values():
                if entity.conversion and not entity.errors:
                    if not summary.get(entity.archive_entity_type):
                        summary[entity.archive_entity_type] = 0
                    summary[entity.archive_entity_type] = summary[entity.archive_entity_type] + 1
        return summary

    def generate_report(self):
        report = {}
        entities = {}
        for entity in self.get_entities():
            entities[entity.id] = {}
            entities[entity.id]['type'] = entity.archive_entity_type
            entities[entity.id]['errors'] = [error.__dict__ for error in entity.errors]
            entities[entity.id]['accession'] = entity.accession
            entities[entity.id]['warnings'] = entity.warnings
            entities[entity.id]['converted_data'] = entity.conversion

            if isinstance(entity, IngestDspEntity) and entity.dsp_json:
                entities[entity.id]['entity_url'] = entity.dsp_json['_links']['self']['href']

        report['entities'] = entities
        report['conversion_summary'] = self.get_conversion_summary()

        return report

    def find_entity(self, alias):
        for entities_dict in self.entities_dict_type.values():
            if entities_dict.get(alias):
                return entities_dict.get(alias)
        return None

    def get_entities(self) -> List[IngestDspEntity]:
        entities = []
        for entity_type, entities_dict in self.entities_dict_type.items():
            if not entities_dict:
                continue
            for alias, entity in entities_dict.items():
                entities.append(entity)
        return entities

    def update(self, entity_type, entities: dict):
        if not self.entities_dict_type.get(entity_type):
            self.entities_dict_type[entity_type] = {}
        self.entities_dict_type[entity_type].update_archive_submission(entities)

    @staticmethod
    def map_from_report(report):
        entity_map = ArchiveEntityMap()
        for key, entity in report.items():
            entity_map.add_entity(IngestDspEntity.map_from_report(key, entity))
        return entity_map

    @staticmethod
    def map_from_ingest_entities(ingest_entities: Iterator[dict]):
        entity_map = ArchiveEntityMap()
        for ingest_entity in ingest_entities:
            entity = IngestDspEntity.map_from_ingest_entity(ingest_entity)
            entity_map.add_entity(entity)
        return entity_map
