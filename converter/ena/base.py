from xml.etree.ElementTree import Element
from abc import ABC, abstractmethod
from json_converter.json_mapper import JsonMapper
from lxml import etree
from enum import Enum
import requests
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig

from converter import fixed_attribute, get_concrete_type
from config import ENA_WEBIN_API_URL, ENA_WEBIN_USERNAME, ENA_WEBIN_PASSWORD


class BaseEnaConverter:
    def __init__(self, ena_type: str):
        self.ena_type = ena_type
        self.xml_spec = None
        self.ena_set: Element = None
        self.__init_is_update()

    def convert(self, entity: dict, additional_attributes: dict = None):
        self.__init_is_update()
        if additional_attributes is None:
            additional_attributes = {}

        self._add_accession_and_alias(self.xml_spec, additional_attributes)
        xml_map = JsonMapper(self._get_entity_content(entity)).map(self.xml_spec)
        root_entity = etree.Element(self.ena_type.upper())
        self.ena_set.append(root_entity)
        self.__add_children(parent=root_entity, children=xml_map)
        self._post_conversion(entity, root_entity)

        return

    def __init_is_update(self):
        self.updated = False

    def init_ena_set(self):
        self.ena_set = etree.XML(f'<{self.ena_type.upper()}_SET />')

    def init_xml_spec(self):
        pass

    def _add_accession_and_alias(self, spec: dict, other_attributes: dict):
        accession = other_attributes.get('accession')
        if accession:
            self.updated = True
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


class XMLType(Enum):
    PROJECT='PROJECT',
    SAMPLE='SAMPLE',
    EXPERIMENT='EXPERIMENT',
    RUN='RUN'


class EnaArchiveException(Exception):
    pass


class EnaModel(ABC):

    PROJECT_ACCESSION_PREFIX="PRJ"
    SAMPLE_ACCESSION_PREFIX="ERS"
    EXPERIMENT_ACCESSION_PREFIX="ERX"
    RUN_ACCESSION_PREFIX="ERR"

    @abstractmethod
    def create_set(self):
        pass

    @abstractmethod
    def create(self):
        pass

    @staticmethod
    def xml_str(model):
        config = SerializerConfig(pretty_print=True)
        serializer = XmlSerializer(config=config)
        return serializer.render(model)

    @staticmethod
    def post(xml_type:XMLType, xml:any, update=False):
        action = 'MODIFY' if update else 'ADD' # default
        response=requests.post(ENA_WEBIN_API_URL, files={xml_type.name: xml}, data={'ACTION': action}, auth=(ENA_WEBIN_USERNAME, ENA_WEBIN_PASSWORD))
        receipt_xml = response.text
        return receipt_xml
