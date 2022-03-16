from copy import deepcopy
from xml.etree.ElementTree import Element

from lxml import etree

from converter import get_value_by_key_path, fixed_attribute
from converter.ena.base import BaseEnaConverter

ADDITIONAL_ATTRIBUTE_KEYS = ['uuid.uuid', 'content.project_core.project_short_name']

STUDY_SPEC = {
    '@center_name': ['', fixed_attribute, 'HCA'],
    'DESCRIPTOR': {
        'STUDY_TITLE': ['project_title'],
        'STUDY_TYPE': {
            '@existing_study_type': ['', fixed_attribute, 'Transcriptome Analysis']
        },
        'STUDY_DESCRIPTION': ['project_description']
    }
}


class EnaStudyConverter(BaseEnaConverter):

    def __init__(self):
        super().__init__(ena_type='Study')

    def init_xml_spec(self):
        self.xml_spec = deepcopy(STUDY_SPEC)

    @staticmethod
    def _post_conversion(entity: dict, xml_element: Element):
        attributes = etree.SubElement(xml_element, 'STUDY_ATTRIBUTES')
        for key in ADDITIONAL_ATTRIBUTE_KEYS:
            key_list: list = key.split('.')
            value: str = get_value_by_key_path(entity, key_list)
            if value:
                BaseEnaConverter._make_attribute(
                    attributes, 'STUDY_ATTRIBUTE', key_list[-1], value)

    @staticmethod
    def _get_entity_content(entity: dict) -> dict:
        return entity.get('content', {}).get('project_core', {})
