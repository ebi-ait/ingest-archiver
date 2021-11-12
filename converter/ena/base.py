from typing import Iterable
from xml.etree.ElementTree import Element

from json_converter.json_mapper import JsonMapper
from lxml import etree
from submission_broker.submission.entity import Entity


class BaseEnaConverter:
    def __init__(self, ena_type: str, xml_spec: dict):
        self.ena_type = ena_type
        self.xml_spec = xml_spec

    def convert(self, entity: dict, additional_attributes: dict = None) -> str:
        ena_set: Element = etree.XML(f'<{self.ena_type.upper()}_SET />')
        self._add_alias_to_additional_attributes(entity, additional_attributes)
        self.add_accession_and_alias(self.xml_spec, additional_attributes)
        xml_map = JsonMapper(self._get_core_attributes(entity)).map(self.xml_spec)
        root_entity = etree.Element(self.ena_type.upper())
        ena_set.append(root_entity)
        self.add_children(parent=root_entity, children=xml_map)
        self.post_conversion(entity, root_entity)
        etree.indent(ena_set, space="    ")
        return self.convert_to_xml_str(ena_set)

    @staticmethod
    def _add_alias_to_additional_attributes(entity: dict, additional_attributes: dict):
        additional_attributes['alias'] =\
            entity.get('content').get('project_core').get('project_short_name') + '_' + entity.get('uuid').get('uuid')

    @staticmethod
    def add_accession_and_alias(spec: dict, other_attributes: dict):
        accession = other_attributes.get('accession')
        if accession:
            spec['@accession'] = ['', BaseEnaConverter.fixed_attribute, accession]

        alias = other_attributes.get('alias')
        if alias:
            spec['@alias'] = ['', BaseEnaConverter.fixed_attribute, alias]

    @staticmethod
    def post_conversion(entity: dict, xml_element: Element):
        pass

    @staticmethod
    def _get_core_attributes(entity: dict) -> dict:
        pass

    @staticmethod
    def add_children(parent: Element, children: dict):
        for name, value in children.items():
            if name.startswith('@'):
                attribute_name = name.lstrip('@')
                parent.attrib[attribute_name] = str(value)
            else:
                element = etree.SubElement(parent, name)
                if isinstance(value, dict):
                    BaseEnaConverter.add_children(parent=element, children=value)
                elif value and str(value):
                    element.text = str(value)

    @staticmethod
    def make_attribute(parent: Element, element_name: str, key: str, value: str, key_name: str = None,
                       value_name: str = None):
        attribute = etree.SubElement(parent, element_name)
        if not key_name:
            key_name = 'TAG'
        attribute_key = etree.SubElement(attribute, key_name)
        attribute_key.text = key

        if not value_name:
            value_name = 'VALUE'
        attribute_value = etree.SubElement(attribute, value_name)
        attribute_value.text = value

    @staticmethod
    def add_link(link: dict, entity: Entity, accession_services: Iterable[str]):
        accession = entity.get_first_accession(accession_services)
        if accession:
            link['@accession'] = ['', BaseEnaConverter.fixed_attribute, accession]
        else:
            link['@refname'] = ['', BaseEnaConverter.fixed_attribute, entity.identifier.index]

    @staticmethod
    def fixed_attribute(*args):
        value = args[1]
        return value

    @staticmethod
    def convert_to_xml_str(element: Element) -> str:
        return etree.tostring(element, xml_declaration=True, pretty_print=True, encoding="UTF-8").decode("UTF-8")
