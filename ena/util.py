import json
import xml
import xmltodict

from xml.etree import ElementTree


def load_xml_dict(filename:str) -> dict:
    with open(filename) as xml_file:
        xml_dict = xmltodict.parse(xml_file.read())
        xml_file.close()
    return xml_dict


def load_xml_dict_from_string(string: str) -> dict:
    return xmltodict.parse(string)


def load_xml_tree_from_string(string: str) -> dict:
    return xml.etree.ElementTree.fromstring(string)


def write_xml(tree: ElementTree.ElementTree, filename: str):
    tree.write(filename, encoding="UTF-8", xml_declaration=True)


def load_json(filename: str):
    with open(filename) as json_file:
        data = json.load(json_file)
    return data


def write_json(data: dict, filename):
    with open(filename, "w") as open_file:
        json.dump(data, open_file, indent=2)


def xml_to_string(tree: ElementTree.ElementTree):
    return ElementTree.tostring(tree.getroot(), encoding='utf8', method='xml')
