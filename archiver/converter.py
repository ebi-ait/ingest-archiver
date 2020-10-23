import logging
import re

from flatten_json import flatten

import archiver.ena
from archiver import biostudies, ena, biosamples
from archiver.dsp_post_process import dsp_attribute, fixed_dsp_attribute
from archiver.instrument_model import to_dsp_name
from conversion.json_mapper import JsonMapper, json_array, json_object
from conversion.post_process import prefix_with, default_to, format_date
from utils import protocols

"""
HCA to DSP JSON Mapping
https://docs.google.com/document/d/1DvF0S9rL0IxnMdsi9P3qUVRt-IOT25KWqjwwIU7C9_s
## TODO: Use SchemaTemplate.replaced_by_latest() to check for template migrations.
"""


class Converter:
    def __init__(self, ontology_api=None):
        self.logger = logging.getLogger(__name__)
        self.field_mapping = {
            "uuid__uuid": "alias",
            "submissionDate": "releaseDate"
        }
        self.alias_prefix = ''
        self.exclude_data = []
        self.exclude_fields_match = ['__schema_type', '__describedBy', '__ontology_label']
        self.ingest_api = None
        self.ontology_api = ontology_api
        self.remove_input_prefix = False
        self.to_lowercase_attributes = False

    def convert(self, hca_data):
        try:
            flattened_hca_data = self._flatten(hca_data)
            extracted_data = self._extract_fields(flattened_hca_data, hca_data)
            converted_data = self._build_output(extracted_data, flattened_hca_data, hca_data=hca_data)
            converted_data = self.rename_attributes(converted_data, hca_data)
            extracted_data["alias"] = f'{self.alias_prefix}{extracted_data["alias"]}'

        except KeyError as e:
            error_message = "Error:" + str(e)
            self.logger.error(error_message)
            raise ConversionError("Conversion Error",
                                  "An error occurred in converting the metadata. Data maybe malformed.",
                                  details={'data': hca_data})
        return converted_data

    def _flatten(self, hca_data):
        input_data = dict(hca_data)

        for key in self.exclude_data:
            if key in input_data:
                del input_data[key]

        flattened = flatten(input_data, '__')

        delete_keys = {}
        if self.exclude_fields_match:
            for key in flattened.keys():
                for keyword in self.exclude_fields_match:
                    if keyword in key:
                        delete_keys[key] = True

        for key in delete_keys.keys():
            del flattened[key]

        return flattened

    def _extract_fields(self, flattened_hca_data, hca_data):
        extracted_data = {}

        for key, new_key in self.field_mapping.items():
            if key in flattened_hca_data:
                extracted_data[new_key] = flattened_hca_data[key]
            else:
                extracted_data[new_key] = ""

        extracted_data["attributes"] = self._extract_attributes(flattened_hca_data)

        for input_key, entity in hca_data.items():
            if isinstance(entity, dict):
                extracted_data["attributes"][f"HCA {input_key.replace('_', ' ').title()} UUID"] = [dict(value=entity["uuid"]["uuid"])]
            elif isinstance(entity, list):
                uuid_list = [e["uuid"]["uuid"] for e in entity]
                extracted_data["attributes"][
                    f"HCA {input_key.replace('_', ' ').title()} UUID's"] = [
                    dict(value=', '.join(uuid_list))]

        return extracted_data

    def _extract_attributes(self, flattened_hca_data):
        attributes = {}
        prefix = "content__"
        ontology_keyword = "__ontology"
        ontology_text_keyword = "__text"

        for key, value in flattened_hca_data.items():
            if re.search(f'__{prefix}', key) and key not in self.field_mapping:
                if ontology_keyword in key:
                    text_field = key.replace(ontology_keyword, ontology_text_keyword)
                    text = flattened_hca_data.get(text_field, '')
                    attr = {
                        "value": text,
                        "terms": [{
                            "url": self.ontology_api.iri_from_obo_id(value)
                        }]
                    }
                    text_field = text_field.replace(prefix, '')
                    name = text_field.replace(ontology_text_keyword, '')
                    attributes[name] = [attr]
                elif ontology_text_keyword in key:
                    # ignore
                    pass
                else:
                    field = key.replace(prefix, '')
                    attr = {
                        "name" : field,
                        "value": value,
                        "terms": []
                    }
                    attributes[attr['name']] = [dict(value=value)]

        return attributes

    def _build_output(self, extracted_data, flattened_hca_data=None, hca_data=None):
        return extracted_data

    def rename_attributes(self, converted_data, hca_data):
        new_attributes = {}
        attributes = converted_data.get('attributes')

        for field, value in attributes.items():
            if '__' in field:
                new_field = field
                if self.remove_input_prefix:
                    split_fields = field.split('__', 1)
                    new_field = split_fields[-1] if split_fields else field

                new_field = new_field.replace('__', ' - ')
                if self.to_lowercase_attributes:
                    new_field = new_field.replace('_', ' ').lower()
                else:
                    new_field = new_field.replace('_', ' ').title()
                new_attributes[new_field] = value
            else:
                new_attributes[field] = value
        converted_data['attributes'] = new_attributes
        return converted_data


# TODO keeping this to not cause trouble with the Archiver script.
class SampleConverter(Converter):

    def __init__(self, ontology_api):
        super(SampleConverter, self).__init__(ontology_api)
        self.logger = logging.getLogger(__name__)

    def convert(self, hca_data):
        return biosamples.convert(hca_data)


class SequencingExperimentConverter(Converter):
    def __init__(self, ontology_api):
        super(SequencingExperimentConverter, self).__init__(ontology_api)
        self.logger = logging.getLogger(__name__)

    def convert(self, hca_data):
        return ena.convert_sequencing_experiment(hca_data)

    # TODO implement
    def _build_links(self, extracted_data, links):
        extracted_data["studyRef"] = {"alias": "{studyAlias.placeholder}"}
        extracted_data["sampleUses"] = [{"sampleRef": {"alias": "{sampleAlias.placeholder}"}}]


# TODO keeping this to not cause trouble with the Archiver script.
class SequencingRunConverter(Converter):
    def __init__(self, ontology_api):
        super(SequencingRunConverter, self).__init__(ontology_api)
        self.logger = logging.getLogger(__name__)

    def convert(self, hca_data):
        return ena.convert_sequencing_run(hca_data)


# TODO keeping this for now to not break the IngestArchiver class
class ProjectConverter(Converter):

    def __init__(self, ontology_api):
        super(ProjectConverter, self).__init__(ontology_api)
        self.logger = logging.getLogger(__name__)

    def convert(self, hca_data):
        return biostudies.convert_project(hca_data)


# TODO keeping this for now to not break the Archiver
class StudyConverter(Converter):

    def __init__(self, ontology_api):
        super(StudyConverter, self).__init__(ontology_api)
        self.logger = logging.getLogger(__name__)

    def convert(self, hca_data):
        return archiver.ena.convert_study(hca_data)


class ConversionError(Exception):
    def __init__(self, expression, message, details=None):
        self.expression = expression
        self.message = message
        self.details = details