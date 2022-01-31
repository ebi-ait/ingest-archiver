from xml.etree.ElementTree import Element

from json_converter.json_mapper import JsonMapper
from lxml import etree

from converter import fixed_attribute, get_concrete_type


class BaseEnaConverter:
    def __init__(self, ena_type: str, xml_spec: dict):
        self.ena_type = ena_type
        self.xml_spec = xml_spec
        self.ena_set: Element = None

    def convert(self, entity: dict, additional_attributes: dict = None):
        if additional_attributes is None:
            additional_attributes = {}

        self._add_accession_and_alias(self.xml_spec, additional_attributes)
        xml_map = JsonMapper(self._get_entity_content(entity)).map(self.xml_spec)
        root_entity = etree.Element(self.ena_type.upper())
        self.ena_set.append(root_entity)
        self.__add_children(parent=root_entity, children=xml_map)
        self._post_conversion(entity, root_entity)

        return

    def init_ena_set(self):
        self.ena_set = etree.XML(f'<{self.ena_type.upper()}_SET />')

    @staticmethod
    def _add_accession_and_alias(spec: dict, other_attributes: dict):
        accession = other_attributes.get('accession')
        if accession:
            spec['@accession'] = ['', fixed_attribute, accession]

        alias = other_attributes.get('alias')
        if alias:
            spec['@alias'] = ['', fixed_attribute, alias]

    @staticmethod
    def _add_alias_to_additional_attributes(entity: dict, additional_attributes: dict):
        pass

    @staticmethod
    def _post_conversion(entity: dict, xml_element: Element):
        pass

    @staticmethod
    def _get_entity_content(entity: dict) -> dict:
        pass

    @staticmethod
    def __add_children(parent: Element, children: dict):
        for name, value in children.items():
            if name.startswith('@'):
                attribute_name = name.lstrip('@')
                parent.attrib[attribute_name] = str(value)
            else:
                element = etree.SubElement(parent, name)
                if isinstance(value, dict):
                    BaseEnaConverter.__add_children(parent=element, children=value)
                elif value and str(value):
                    element.text = str(value)

    @staticmethod
    def _make_attribute(parent: Element, element_name: str, key: str, value: str, key_name: str = None,
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

    def convert_entity_to_xml_str(self) -> str:
        converted_ena_entity = self.ena_set
        if len(converted_ena_entity) < 1:
            return ''
        etree.indent(converted_ena_entity, space="    ")

        return etree.tostring(converted_ena_entity, xml_declaration=True, pretty_print=True, encoding="UTF-8")

    @staticmethod
    def _get_scientific_name(args):
        return args[0].get('ontology_label', None)

    @staticmethod
    def _get_taxon_id(args):
        return args[0]

    @staticmethod
    def _derive_concrete_type(*args):
        schema_url = args[0]
        concrete_type = get_concrete_type(schema_url)
        return concrete_type
