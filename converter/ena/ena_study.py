from xml.etree.ElementTree import Element

from lxml import etree

from converter.ena.base import BaseEnaConverter

ADDITIONAL_ATTRIBUTE_KEYS = ['uuid.uuid', 'content.project_core.project_short_name', 'technology']


class EnaStudyConverter(BaseEnaConverter):

    def __init__(self):
        study_spec = {
            '@center_name': ['', BaseEnaConverter.fixed_attribute, 'HCA'],
            'DESCRIPTOR': {
                'STUDY_TITLE': ['project_title'],
                'STUDY_TYPE': {
                    '@existing_study_type': ['', BaseEnaConverter.fixed_attribute, 'Transcriptome Analysis']
                },
                'STUDY_DESCRIPTION': ['project_description']
            }
        }
        super().__init__(ena_type='Study', xml_spec=study_spec)

    @staticmethod
    def post_conversion(entity: dict, xml_element: Element):
        attributes = etree.SubElement(xml_element, 'STUDY_ATTRIBUTES')
        for key in ADDITIONAL_ATTRIBUTE_KEYS:
            key_list: list = key.split('.')
            value: str = EnaStudyConverter._get_value_by_key_path(entity, key_list)
            if value:
                BaseEnaConverter.make_attribute(
                    attributes, 'STUDY_ATTRIBUTE', key_list[-1], value)

    @staticmethod
    def _add_alias_to_additional_attributes(entity: dict, additional_attributes: dict):
        additional_attributes['alias'] =\
            entity.get('content').get('project_core').get('project_short_name') + '_' + entity.get('uuid').get('uuid')

    @staticmethod
    def _get_core_attributes(entity: dict) -> dict:
        return entity.get('content').get('project_core')
