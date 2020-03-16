import logging
import re

from flatten_json import flatten

from archiver import biostudies_project, ena_sequencing_experiment
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
                            "url": self.ontology_api.expand_curie(value)
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


class SampleConverter(Converter):

    def __init__(self, ontology_api):
        super(SampleConverter, self).__init__(ontology_api)
        self.logger = logging.getLogger(__name__)
        self.field_mapping = {
            "biomaterial__uuid__uuid": "alias",
            "biomaterial__content__biomaterial_core__biomaterial_name": "title",
            "biomaterial__content__biomaterial_core__biomaterial_description": "description",
            "biomaterial__content__biomaterial_core__ncbi_taxon_id__0": "taxonId",
            "biomaterial__submissionDate": "releaseDate"
        }

        # TODO local mapping for now, ideally this should be an OLS lookup
        # TODO what's taxon id for mouse
        self.taxon_map = {
            "9606": "Homo sapiens",
            "10090": "Mus musculus"
        }
        self.exclude_data = ['genus_species']
        self.exclude_fields_match = ['__schema_type', '__describedBy',
                                     '__ontology_label',
        # FIXME only donors contain this info but this is redundant with taxonId, removing this if it exists
                                     'biomaterial__content__genus_species__0__ontology',
                                     'biomaterial__content__genus_species__0__text']
        self.remove_input_prefix = True

    def convert(self, hca_data):
        def taxon(*args):
            ontology_item = args[0]
            genus_species = ontology_item[0]
            return genus_species.get('ontology_label')

        def taxon_id(*args):
            taxon_ids = args[0]
            return taxon_ids[0] if taxon_ids and len(taxon_ids) > 0 else None

        def derive_concrete_type(*args):
            schema_url = args[0]
            concrete_type = schema_url.split('/')[-1]
            return dsp_attribute(concrete_type)

        return JsonMapper(hca_data).map({
            '$on': 'biomaterial',
            'alias': ['uuid.uuid'],
            'attributes': {
                'Biomaterial Core - Biomaterial Id': ['content.biomaterial_core.biomaterial_id', dsp_attribute],
                'HCA Biomaterial Type': ['content.describedBy', derive_concrete_type],
                'HCA Biomaterial UUID': ['uuid.uuid', dsp_attribute],
                'Is Living': ['content.is_living', dsp_attribute],
                'Medical History - Smoking History': ['content.medical_history.smoking_history', dsp_attribute],
                'Sex': ['content.sex', dsp_attribute],
                'project': ['', fixed_dsp_attribute, 'Human Cell Atlas']
            },
            'description': ['content.biomaterial_core.biomaterial_description'],
            'releaseDate': ['submissionDate', format_date],
            # this is to work around this being constantly empty
            'sampleRelationships': ['sampleRelationships', default_to, []],
            'taxon': ['content.genus_species', taxon],
            'taxonId': ['content.biomaterial_core.ncbi_taxon_id', taxon_id],
            'title': ['content.biomaterial_core.biomaterial_name']
        })

    def _build_output(self, extracted_data, flattened_hca_data, hca_data):
        extracted_data["releaseDate"] = extracted_data["releaseDate"].split('T')[0]
        extracted_data["sampleRelationships"] = []
        taxon_id = str(extracted_data.get("taxonId", ''))
        extracted_data["taxon"] = self.taxon_map.get(taxon_id)

        if not extracted_data["taxon"]:
            raise ConversionError("Sample Conversion Error",
                                  f"Sample Converter find the taxon text from taxon id, {taxon_id}",
                                  details={'taxon_id': taxon_id})

        # non required fields
        if "title" in extracted_data:
            extracted_data["title"] = extracted_data["title"]

        if not extracted_data.get("attributes"):
            extracted_data["attributes"] = {}

        extracted_data["taxon"] = self.taxon_map.get(str(extracted_data["taxonId"]))

        if not extracted_data["taxon"]:
            raise ConversionError("Sample Conversion Error", "Sample Converter find the taxon text from taxonId.")

        concrete_type = self._get_concrete_type(hca_data.get('biomaterial'))
        extracted_data["attributes"]["HCA Biomaterial Type"] = [dict(value=concrete_type)]
        extracted_data["attributes"]["project"] = [dict(value="Human Cell Atlas")]

        return extracted_data

    def _get_concrete_type(self, entity):
        concrete_type = self.ingest_api.get_concrete_entity_type(entity)
        return concrete_type


class SequencingExperimentConverter(Converter):
    def __init__(self, ontology_api):
        super(SequencingExperimentConverter, self).__init__(ontology_api)
        self.logger = logging.getLogger(__name__)

    def convert(self, hca_data):
        return ena_sequencing_experiment.convert(hca_data)

    # TODO implement
    def _build_links(self, extracted_data, links):
        extracted_data["studyRef"] = {"alias": "{studyAlias.placeholder}"}
        extracted_data["sampleUses"] = [{"sampleRef": {"alias": "{sampleAlias.placeholder}"}}]


class SequencingRunConverter(Converter):
    def __init__(self, ontology_api):
        super(SequencingRunConverter, self).__init__(ontology_api)
        self.logger = logging.getLogger(__name__)

        self.field_mapping = {
            "process__uuid__uuid": "alias",
            "process__content__process_core__process_name": "title",
            "process__content__process_core__process_description": "description"
        }

        self.file_format = {
            'fastq.gz': 'fastq',
            'bam': 'bam',
            'cram': 'cram',
        }

        self.alias_prefix = 'sequencingRun_'
        self.exclude_data = ['manifest_id', 'library_preparation_protocol']

    def convert(self, hca_data):
        converted_data = super(SequencingRunConverter, self).convert(hca_data)

        files = []
        if protocols.is_10x(hca_data.get("library_preparation_protocol")):
            files = [{
                'name': f"{hca_data['manifest_id']}.bam",
                'type': 'bam'
            }]
        else:
            for file in hca_data['files']:
                flattened_file = self._flatten(file)
                files.append({
                    'name': flattened_file.get('content__file_core__file_name'),
                    'type': self.file_format[flattened_file.get('content__file_core__format')]
                })

        converted_data['files'] = files

        return converted_data

    def _build_output(self, extracted_data, flattened_hca_data, hca_data=None):
        self._build_links(extracted_data, {})

        return extracted_data

    # TODO implement
    def _build_links(self, extracted_data, links):
        extracted_data["assayRefs"] = {"alias": "{assayAlias.placeholder}"}


# TODO keeping this for now to not break the IngestArchiver class
class ProjectConverter(Converter):

    def __init__(self, ontology_api):
        super(ProjectConverter, self).__init__(ontology_api)
        self.logger = logging.getLogger(__name__)

    def convert(self, hca_data):
        return biostudies_project.convert(hca_data)


class StudyConverter(Converter):

    def __init__(self, ontology_api):
        super(StudyConverter, self).__init__(ontology_api)
        self.logger = logging.getLogger(__name__)
        self.study_prefix = 'study_'

    def convert(self, hca_data):
        # TODO maybe extract this to a separate component
        return JsonMapper(hca_data).map({
            '$on': 'project',
            'alias': ['uuid.uuid', prefix_with, self.study_prefix],
            'attributes': {
                'HCA Project UUID': ['uuid.uuid', dsp_attribute],
                'Project Core - Project Short Name': ['content.project_core.project_short_name', dsp_attribute],
                'study_type': ['', fixed_dsp_attribute, 'Transcriptome Analysis'],
                'study_abstract': ['content.project_core.project_description', dsp_attribute],
            },
            'title': ['content.project_core.project_title'],
            'description': ['content.project_core.project_description'],
            'projectRef': {
                'alias': ['', default_to, '{projectAlias.placeholder}']
            }
        })


class ConversionError(Exception):
    def __init__(self, expression, message, details=None):
        self.expression = expression
        self.message = message
        self.details = details
