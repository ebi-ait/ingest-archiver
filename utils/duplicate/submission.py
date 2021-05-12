from hca.submission import HcaSubmission, Entity, HandleCollision, ACCESSION_SPEC


class DuplicateSubmission(HcaSubmission):
    def __init__(self):
        self.biosamples = {}
        super().__init__(collider=HandleCollision.OVERWRITE)

    def __get_accessions_from_attributes(self, entity: Entity):
        for service, mapping_list in ACCESSION_SPEC.items():
            accession_key = mapping_list[0]
            DuplicateSubmission.__remove_last_descendant(entity.attributes, accession_key)

    @staticmethod
    def __remove_last_descendant(attributes: dict, descendants: str):
        child_key, _, child_descendants = descendants.partition('.')
        if child_key in attributes:
            if not child_descendants:
                return attributes.pop(child_key)
            child_attributes = attributes[child_key]
            accession = DuplicateSubmission.__remove_last_descendant(child_attributes, child_descendants)
            if len(child_attributes) == 0:
                attributes.pop(child_key)
            return accession
