import logging
import re
import requests

from flatten_json import flatten

from archiver.ingestapi import IngestAPI

"""
HCA to USI JSON Mapping
https://docs.google.com/document/d/1yXTelUt-CvlI7-Jkh7K_NCPIBfhRXMvjT4wRkyxpIN0/edit#
"""


class Converter:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.field_mapping = {
            "uuid__uuid": "alias",
            "submissionDate": "releaseDate"
        }
        self.alias_prefix = ''
        self.exclude_data = []
        self.exclude_fields_match = ['__schema_type', '__describedBy']
        self.ingest_api = None

    def convert(self, hca_data):
        try:
            flattened_hca_data = self._flatten(hca_data)
            extracted_data = self._extract_fields(flattened_hca_data, hca_data)
            converted_data = self._build_output(extracted_data, flattened_hca_data, hca_data=hca_data)
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

        if self.exclude_data:
            for key in self.exclude_data:
                if key in input_data:
                    del input_data[key]

        flattened = flatten(input_data, '__')

        delete_keys = []
        if self.exclude_fields_match:
            for key in flattened.keys():
                for keyword in self.exclude_fields_match:
                    if keyword in key:
                        delete_keys.append(key)

        for key in delete_keys:
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

        try:
            for input_key, entity in hca_data.items():
                if isinstance(entity, dict):
                    extracted_data["attributes"][f"HCA {input_key.replace('_', ' ').title()} UUID"] = [dict(value=entity["uuid"]["uuid"])]
                elif isinstance(entity, list):
                    uuid_list = [e["uuid"]["uuid"] for e in entity]
                    extracted_data["attributes"][
                        f"HCA {input_key.replace('_', ' ').title()} UUID's"] = [
                        dict(value=', '.join(uuid_list))]
        except Exception as e:
            bp=0

        return extracted_data

    def _extract_attributes(self, flattened_hca_data):
        attributes = {}
        prefix = "content__"

        for key, value in flattened_hca_data.items():
            if re.search(prefix, key) and key not in self.field_mapping:
                attr = {
                    "name": key.replace(prefix, ""),
                    "value": value,
                    "terms": []
                }
                attributes[attr['name']] = [dict(value=value)]

        return attributes

    def _build_output(self, extracted_data, flattened_hca_data=None, hca_data=None):
        return extracted_data


class SampleConverter(Converter):

    def __init__(self):
        super(SampleConverter, self).__init__()
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

        # TODO only donors contain this info but this is redundant with taxonId, removing this if it exists
        if extracted_data["attributes"].get("biomaterial__genus_species__0__text"):
            del extracted_data["attributes"]["biomaterial__genus_species__0__text"]

        if extracted_data["attributes"].get("biomaterial__genus_species__0__ontology"):
            del extracted_data["attributes"]["biomaterial__genus_species__0__ontology"]

        if not extracted_data["taxon"]:
            raise ConversionError("Sample Conversion Error", "Sample Converter find the taxon text from taxonId.")

        concrete_type = self._get_concrete_type(hca_data.get('biomaterial'))
        extracted_data["attributes"]["HCA Biomaterial Type"] = [dict(value=concrete_type)]

        return extracted_data

    def _get_concrete_type(self, entity):
        concrete_type = self.ingest_api.get_concrete_entity_type(entity)
        return concrete_type


class SequencingExperimentConverter(Converter):
    def __init__(self):
        super(SequencingExperimentConverter, self).__init__()
        self.logger = logging.getLogger(__name__)
        self.alias_prefix = 'sequencingExperiment_'

        self.library_selection_mapping = {
            "poly-dT": "Oligo-dT",
            "random": "RANDOM",
        }

        self.instrument_model_map = {
            "illumina genome analyzer": {
                "platform_type": "ILLUMINA",
                "intrument_model": "Illumina Genome Analyzer"
            },
            "illumina genome analyzer ii": {
                "platform_type": "ILLUMINA",
                "intrument_model": "Illumina Genome Analyzer II"
            },
            "illumina genome analyzer iix": {
                "platform_type": "ILLUMINA",
                "intrument_model": "Illumina Genome Analyzer IIx"
            },
            "illumina hiseq 2500": {
                "platform_type": "ILLUMINA",
                "intrument_model": "Illumina HiSeq 2500"
            },
            "illumina hiseq 2000": {
                "platform_type": "ILLUMINA",
                "intrument_model": "Illumina HiSeq 2000"
            },
            "illumina hiseq 1500": {
                "platform_type": "ILLUMINA",
                "intrument_model": "Illumina HiSeq 1500"
            },
            "illumina hiseq 1000": {
                "platform_type": "ILLUMINA",
                "intrument_model": "Illumina HiSeq 1000"
            },
            "illumina miseq": {
                "platform_type": "ILLUMINA",
                "intrument_model": "Illumina MiSeq"
            },
            "illumina hiscansq": {
                "platform_type": "ILLUMINA",
                "intrument_model": "Illumina HiScanSQ"
            },
            "hiseq x ten": {
                "platform_type": "ILLUMINA",
                "intrument_model": "HiSeq X Ten",
                "synonymns": [
                    "illumina hiseq x 10"
                ]
            },
            "nextseq 500": {
                "platform_type": "ILLUMINA",
                "intrument_model": "NextSeq 500",
                "synonymns": [
                    "illumina nextseq 500"
                ]
            },
            "hiseq x five": {
                "platform_type": "ILLUMINA",
                "intrument_model": "HiSeq X Five",
            },
            "illumina hiseq 3000": {
                "platform_type": "ILLUMINA",
                "intrument_model": "Illumina HiSeq 3000"
            },
            "illumina Hiseq 4000": {
                "platform_type": "ILLUMINA",
                "intrument_model": "Illumina HiSeq 4000"
            },
            "nextseq 550": {
                "platform_type": "ILLUMINA",
                "intrument_model": "NextSeq 550",
            }
        }

        self.field_mapping = {
            "process__uuid__uuid": "alias",
            "sequencing_protocol__content__protocol_core__protocol_name": "title",
            "sequencing_protocol__content__protocol_core__protocol_description": "description"
        }

    def _build_output(self, extracted_data, flattened_hca_data, hca_data=None):
        extracted_data["studyRef"] = {}
        extracted_data["sampleUses"] = []

        if not extracted_data.get("attributes"):
            extracted_data["attributes"] = {}
        extracted_data["attributes"]["library_strategy"] = [dict(value="OTHER")]
        extracted_data["attributes"]["library_source"] = [dict(value="TRANSCRIPTOMIC SINGLE CELL")]

        primer = flattened_hca_data.get("library_preparation_protocol__content__primer")
        if primer:
            extracted_data["attributes"]["library_selection"] = [dict(value=self.library_selection_mapping.get(primer, "unspecified"))]

        paired_end = flattened_hca_data.get("sequencing_protocol__content__paired_end")
        if paired_end:
            extracted_data["attributes"]["library_layout"] = [dict(value="PAIRED")]

            # TODO put 0 as default as we don't really capture this in HCA but there's no way to specify 'unspecified'
            extracted_data["attributes"]["nominal_length"] = [dict(value="0")]
            extracted_data["attributes"]["nominal_sdev"] = [dict(value="0")]
        else:
            extracted_data["attributes"]["library_layout"] = [dict(value="SINGLE")]

        # must correctly match ENA enum values
        instr_model_text = flattened_hca_data.get("sequencing_protocol__content__instrument_manufacturer_model__text")
        instrument_model_obj = self.instrument_model_map.get(instr_model_text.lower(), {})
        instrument_model = instrument_model_obj.get('intrument_model', 'unspecified')
        platform_type = instrument_model_obj.get('platform_type', 'unspecified')

        for key, obj in self.instrument_model_map.items():
            synonyms = obj.get("synonymns")
            if synonyms and instr_model_text.lower() in synonyms:
                instrument_model = obj.get('intrument_model', 'unspecified')
                platform_type = obj.get('platform_type', 'unspecified')

        extracted_data["attributes"]["instrument_model"] = [dict(value=instrument_model)]
        extracted_data["attributes"]["platform_type"] = [dict(value=platform_type)]


        extracted_data["attributes"]["design_description"] = [dict(value="unspecified")]

        library_name = flattened_hca_data.get("input_biomaterial__content__biomaterial_core__biomaterial_id", "")
        if not library_name:
            raise ConversionError("Sequencing Experiment Conversion Error",
                                  "There is no id found for the input biomaterial.")

        extracted_data["attributes"]["library_name"] = [dict(value=library_name)]

        self._build_links(extracted_data, {})

        return extracted_data

    # TODO implement
    def _build_links(self, extracted_data, links):
        extracted_data["studyRef"] = {"alias": "{studyAlias.placeholder}"}
        extracted_data["sampleUses"] = [{"sampleRef": {"alias": "{sampleAlias.placeholder}"}}]


class SequencingRunConverter(Converter):
    def __init__(self):
        super(SequencingRunConverter, self).__init__()
        self.logger = logging.getLogger(__name__)

        self.field_mapping = {
            "process__uuid__uuid": "alias",
            "process__content__process_core__process_name": "title",
            "process__content__process_core__process_description": "description"
        }

        self.ONTOLOGY_10x = "EFO:0009310"

        self.file_format = {
            'fastq.gz': 'fastq',
            'bam': 'bam',
            'cram': 'cram',
        }

        self.alias_prefix = 'sequencingRun_'
        self.exclude_data = ['bundle_uuid', 'library_preparation_protocol']

    def convert(self, hca_data):
        converted_data = super(SequencingRunConverter, self).convert(hca_data)

        files = []
        lib_prep = hca_data.get("library_preparation_protocol", {})
        content = lib_prep.get("content", {})
        library_const_approach_obj = content.get("library_construction_approach", {})
        library_const_approach = library_const_approach_obj.get('ontology')

        if library_const_approach and library_const_approach == self.ONTOLOGY_10x:
            files = [{
                'name': f"{hca_data['bundle_uuid']}.bam",
                'type': 'bam'
            }]
        else:
            for file in hca_data['files']:
                flattened_file = self._flatten(file)
                files.append({
                    'name': flattened_file.get('content__file_core__file_name'),
                    'type': self.file_format[flattened_file.get('content__file_core__file_format')]
                })

        converted_data['files'] = files

        return converted_data

    def _build_output(self, extracted_data, flattened_hca_data, hca_data=None):
        self._build_links(extracted_data, {})

        return extracted_data

    # TODO implement
    def _build_links(self, extracted_data, links):
        extracted_data["assayRefs"] = {"alias": "{assayAlias.placeholder}"}


class ProjectConverter(Converter):

    def __init__(self):
        super(ProjectConverter, self).__init__()
        self.logger = logging.getLogger(__name__)
        self.field_mapping = {
            "project__uuid__uuid": "alias",
            "project__content__project_core__project_title": "title",
            "project__content__project_core__project_description": "description",
            "project__submissionDate": "releaseDate"
        }
        self.alias_prefix = 'project_'
        self.exclude_data = ['contributors', 'publications']
        self.exclude_fields_match = ['__schema_type', '__describedBy',
                                     '__contributors', '__publications']

    def _build_output(self, extracted_data, flattened_hca_data, hca_data=None):
        # TODO BioStudies minimum length
        title_len = len(extracted_data["title"])
        MIN_LEN = 25
        DELIM = ' | '
        if title_len < MIN_LEN:
            prefix = "HCA project: "
            extracted_data["title"] = prefix + extracted_data["title"]

        extracted_data["releaseDate"] = extracted_data["releaseDate"].split('T')[0]
        contacts = []
        contributors = hca_data['project']['content'].get('contributors', [])
        for contributor in contributors:
            contact = {
                "orcid": contributor.get("orcid_id", ""),
                "firstName": contributor.get("contact_name", ""),
                "middleInitials": "",
                "lastName": "",
                "email": contributor.get("email", ""),
                "address": contributor.get("address", ""),
                "affiliation": contributor.get("institution", ""),
                "phone": contributor.get("phone", ""),

            }
            contacts.append(contact)
        extracted_data["contacts"] = contacts

        hca_publications = hca_data['project']['content'].get('publications', [])
        publications = []
        for hca_publication in hca_publications:
            publication = {
                "pubmedId": hca_publication.get("pmid", ""),
                "doi": hca_publication.get("doi", ""),
                "articleTitle": hca_publication.get("publication_title", ""),
                "authors": f"{DELIM}".join(hca_publication.get("authors", []))
            }
            publications.append(publication)
        extracted_data["publications"] = publications
        return extracted_data


class StudyConverter(Converter):

    def __init__(self):
        super(StudyConverter, self).__init__()
        self.logger = logging.getLogger(__name__)
        self.field_mapping = {
            "project__uuid__uuid": "alias",
            "project__content__project_core__project_title": "title",
            "project__content__project_core__project_description": "description"
        }
        self.alias_prefix = 'study_'
        self.exclude_data = ['contributors', 'publications']
        self.exclude_fields_match = ['__schema_type', '__describedBy', '__contributors', '__publications']

    def _build_output(self, extracted_data, flattened_hca_data, hca_data=None):
        if not extracted_data.get("attributes"):
            extracted_data["attributes"] = {}

        extracted_data["attributes"]["study_type"] = [dict(value="Transcriptome Analysis")]
        description = extracted_data['description']
        extracted_data["attributes"]["study_abstract"] = [dict(value=description)]

        self._build_links(extracted_data, {})
        return extracted_data

    def _build_links(self, extracted_data, links):
        extracted_data["projectRef"] = {"alias": "{projectAlias.placeholder}"}


class ConversionError(Exception):
    def __init__(self, expression, message, details=None):
        self.expression = expression
        self.message = message
        self.details = details
