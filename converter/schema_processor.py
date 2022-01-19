import csv
import json
import os
from urllib.request import urlopen


class SchemaProcessor:

    def get_attributes_from_schema(self, schema_path: str, prefix: str = '', keys_to_skip: list = None):
        schema: dict = self.__load_schema(schema_path)
        attributes: dict = schema.get('properties')
        attribute_properties = []
        for attribute_name, attribute_value in attributes.items():
            ref = SchemaProcessor.__get_ref(attribute_value)
            attribute_name = f'{prefix}.{attribute_name}' if prefix else attribute_name
            attribute_property = []
            if ref is None:
                attribute_property.append(attribute_name)
                attribute_property.append(attribute_value.get("type"))
                attribute_property.append(f'{prefix} version: {schema_path.split("/")[-2]}')
                attribute_properties.append(attribute_property)
            else:
                attribute_properties.extend(self.get_attributes_from_schema(ref, attribute_name))
        return attribute_properties

    @staticmethod
    def write_attribute_properties_to_csv(attribute_properties: list, file_name: str, path_to_file: str = 'csv'):
        if not os.path.exists(path_to_file):
            os.makedirs(path_to_file)
        with open(f'{path_to_file}/{file_name}', 'w') as result_file:
            wr = csv.writer(result_file, dialect='excel')
            wr.writerows(attribute_properties)

    @staticmethod
    def __load_schema(schema_path):
        with urlopen(schema_path) as response:
            data_json = json.loads(response.read())

        return data_json

    @staticmethod
    def __get_ref(attribute_value):
        ref = attribute_value.get('$ref', None)
        if ref is None:
            ref = attribute_value.get('items', {}).get('$ref', None)

        return ref
