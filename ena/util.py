import json
import xml
import xmltodict


def load_xml(filename) -> dict:
    with open(filename) as xml_file:
        xml_dict = xmltodict.parse(xml_file.read())
        xml_file.close()
    return xml_dict


def load_xml_from_string(text: str) -> dict:
    return xml.etree.ElementTree.fromstring(text)


def write_xml(tree, filename):
    tree.write(filename, encoding="UTF-8", xml_declaration=True)


def load_json(filename):
    with open(filename) as json_file:
        data = json.load(json_file)
    return data


def write_json(data: dict, filename):
    with open(filename, "w") as open_file:
        json.dump(data, open_file, indent=2)
