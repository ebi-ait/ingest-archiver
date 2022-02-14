from json_converter.json_mapper import JsonMapper
from submission_broker.submission.entity import Entity


class AccessionMapper:
    mapping: [str]
    type: str

    def __init__(self, mapping: [str], accession_type: str):
        self.mapping = mapping
        self.type = accession_type

    @staticmethod
    def set_accession_by_attribute_location(accession, accession_location, accession_type, entity):
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

    @staticmethod
    def set_accessions_from_attributes(entity: Entity):
        entity_type = entity.identifier.entity_type
        for service, accession_map_by_entity_type in accession_spec.items():
            accession_mapper = accession_map_by_entity_type.get(entity_type)
            if accession_mapper:
                accession_mappers_by_archive = accession_spec.get(service)
                accession_mapper = accession_mappers_by_archive.get(entity_type)
                accession_location = accession_mapper.mapping
                accession = JsonMapper(entity.attributes).map({entity_type: accession_location}).get(entity_type)
                if accession:
                    entity.add_accession(service, accession)


accession_spec = {
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
