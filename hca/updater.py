from typing import Iterable

from ingest.api.ingestapi import IngestApi
from hca.submission import HcaSubmission, Entity


class HcaUpdater:
    def __init__(self, ingest: IngestApi):
        self.__ingest = ingest

    def update_submission(self, submission: HcaSubmission):
        for entity_type in submission.get_entity_types():
            self.update_entity_type(submission, entity_type)

    def update_entity_type(self, submission: HcaSubmission, entity_type: str):
        self.update_entities(submission.get_entities(entity_type))

    def update_entities(self, entities: Iterable[Entity]):
        for entity in entities:
            self.update_entity(entity)

    def update_entity(self, entity: Entity):
        self_link = HcaSubmission.get_link(entity.attributes, 'self')
        self.__ingest.patch(self_link, entity.attributes)
