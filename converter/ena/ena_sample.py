from xml.etree.ElementTree import Element

from lxml import etree

from converter.ena.base import BaseEnaConverter

ATTRIBUTE_KEYS_TO_SKIP = [
    'describedBy', 'schema_version', 'schema_type', 'provenance', 'biomaterial_core',
    'internal_anatomical_structures',  # imaged_specimen
    'genus_species', 'model_organ', 'model_organ_part', 'age_unit', 'size_unit',  # organoid
    'cell_cycle', 'cell_morphology', 'growth_conditions', 'cell_type', 'tissue', 'disease', 'publication', 'timecourse',  # cell_line
    'human_specific', 'mouse_specific', 'organism_age_unit', 'development_stage', 'diseases', 'death',
    'familial_relationships', 'medical_history', 'gestational_age', 'gestational_age_unit', 'height_unit', 'weight_unit',  # donor_organism
    'organ', 'organ_parts', 'state_of_specimen', 'preservation_storage', 'purchased_specimen',  # specimen_from_organism
    'selected_cell_types', 'plate_based_sequencing'   # cell_suspension
]

# ADDITIONAL_ATTRIBUTE_KEYS = ['uuid.uuid', 'estimated_cell_count', 'plate_based_sequencing', 'timecourse',
#                              'overview_images', 'slice_thickness',  # imaged_specimen
#                              'age', 'size', 'morphology', 'embedded_in_matrigel', 'growth_environment',
#                              'input_aggregate_cell_count', 'stored_oxygen_levels',  # organoid
#                              'supplier', 'catalog_number', 'lot_number', 'catalog_url', 'type'  # cell_line
#                              ]


class EnaSampleConverter(BaseEnaConverter):

    def __init__(self):
        sample_spec = {
            '@center_name': ['', BaseEnaConverter.fixed_attribute, 'HCA'],
            'TITLE': ['biomaterial_core.biomaterial_name'],
            'SAMPLE_NAME': {
                'TAXON_ID': ['biomaterial_core.ncbi_taxon_id', BaseEnaConverter.get_taxon_id],
                'SCIENTIFIC_NAME': ['genus_species', BaseEnaConverter.get_scientific_name]
            },
            'DESCRIPTION': ['biomaterial_core.biomaterial_description']
        }
        super().__init__(ena_type='Sample', xml_spec=sample_spec)

    def post_conversion(self, entity: dict, xml_element: Element):
        attributes = etree.SubElement(xml_element, 'SAMPLE_ATTRIBUTES')
        entity_content = entity.get('content')
        for key in entity_content:
            if key in ATTRIBUTE_KEYS_TO_SKIP:
                continue
            key_list: list = key.split('.')
            value: str = self._get_value_by_key_path(entity_content, key_list)
            if value:
                BaseEnaConverter.make_attribute(
                    attributes, 'SAMPLE_ATTRIBUTE', key_list[-1], value)

    @staticmethod
    def __add_scientific_name():
        pass

    @staticmethod
    def _add_alias_to_additional_attributes(entity: dict, additional_attributes: dict):
        additional_attributes['alias'] = \
            entity.get('content').get('biomaterial_core').get('biomaterial_id') + '_' + entity.get('uuid').get('uuid')

    @staticmethod
    def _get_core_attributes(entity: dict) -> dict:
        return entity.get('content')
