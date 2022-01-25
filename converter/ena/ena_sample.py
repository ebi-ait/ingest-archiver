from xml.etree.ElementTree import Element

from lxml import etree

from converter.ena.base import BaseEnaConverter


HCA_TO_ENA_SAMPLE_ATTRIBUTES = {
    'content.biomaterial_core.biomaterial_id': 'Biomaterial Core - Biomaterial Id',
    'uuid.uuid': 'HCA Biomaterial UUID',
    'content.is_living': 'Is Living',
    'content.medical_history.smoking_history': 'Medical History - Smoking History',
    'content.sex': 'Sex'
}


class EnaSampleConverter(BaseEnaConverter):

    def __init__(self):
        sample_spec = {
            '@center_name': ['', BaseEnaConverter._fixed_attribute, 'HCA'],
            'TITLE': ['biomaterial_core.biomaterial_name'],
            'SAMPLE_NAME': {
                'TAXON_ID': ['biomaterial_core.ncbi_taxon_id', BaseEnaConverter._get_taxon_id],
                'SCIENTIFIC_NAME': ['genus_species', BaseEnaConverter._get_scientific_name]
            },
            'DESCRIPTION': ['biomaterial_core.biomaterial_description']
        }
        super().__init__(ena_type='Sample', xml_spec=sample_spec)

    def _post_conversion(self, entity: dict, xml_element: Element):
        attributes = etree.SubElement(xml_element, 'SAMPLE_ATTRIBUTES')
        EnaSampleConverter.__add_sample_type_as_attribute(attributes, entity)
        for hca_name, ena_name in HCA_TO_ENA_SAMPLE_ATTRIBUTES.items():
            key_list: list = hca_name.split('.')
            value: str = self._get_value_by_key_path(entity, key_list)
            if value:
                BaseEnaConverter._make_attribute(
                    attributes, 'SAMPLE_ATTRIBUTE', ena_name, value)
        EnaSampleConverter.__add_project_name_as_attribute(attributes)

    @staticmethod
    def __add_sample_type_as_attribute(attributes, entity):
        sample_type = BaseEnaConverter._derive_concrete_type(entity.get('content').get('describedBy'))
        BaseEnaConverter._make_attribute(
            attributes, 'SAMPLE_ATTRIBUTE', 'HCA Biomaterial Type', sample_type)

    @staticmethod
    def __add_project_name_as_attribute(attributes):
        BaseEnaConverter._make_attribute(
            attributes, 'SAMPLE_ATTRIBUTE', 'project', 'Human Cell Atlas')

    @staticmethod
    def _get_entity_content(entity: dict) -> dict:
        return entity.get('content')
