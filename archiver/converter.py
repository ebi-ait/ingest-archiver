import logging
import re

from flatten_json import flatten


class ConversionError(Exception):
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message


class Converter:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.field_mapping = {
            "uuid__uuid": "alias",
            "submissionDate": "releaseDate"
        }

    def convert(self, hca_data):
        try:
            flattened_hca_data = flatten(hca_data, '__')
            extracted_data = self._extract_fields(flattened_hca_data)
            converted_data = self._build_output(extracted_data, flattened_hca_data)
        except KeyError as e:
            error_message = "Error:" + str(e)
            self.logger.error(error_message)
            raise ConversionError("Conversion Error",
                                  "An error occurred in converting the metadata. Data maybe malformed.")
        return converted_data

    def _extract_fields(self, flattened_hca_data):
        extracted_data = {"attributes": self._extract_attributes(flattened_hca_data)}

        for key, new_key in self.field_mapping.items():
            if key in flattened_hca_data:
                extracted_data[new_key] = flattened_hca_data[key]
            else:
                self.logger.warning(key + ' is not found in the metadata.')

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

    def _build_output(self, extracted_data):
        return extracted_data


class SampleConverter(Converter):

    def __init__(self):
        super(SampleConverter, self).__init__()
        self.logger = logging.getLogger(__name__)
        self.field_mapping = {
            "uuid__uuid": "alias",
            "content__biomaterial_core__biomaterial_name": "title",
            "content__biomaterial_core__ncbi_taxon_id__0": "taxonId",
            "submissionDate": "releaseDate"
        }

    def _build_output(self, extracted_data, flattened_hca_data):
        extracted_data["releaseDate"] = extracted_data["releaseDate"].split('T')[0]
        extracted_data["sampleRelationships"] = []
        extracted_data["description"] = ""
        # non required fields
        if "title" in extracted_data:
            extracted_data["title"] = extracted_data["title"]

        return extracted_data


class AssayConverter(Converter):
    def __init__(self):
        super(AssayConverter, self).__init__()
        self.logger = logging.getLogger(__name__)
        self.library_selection_mapping = {
            "poly-dt": "Oligo-dT",
            "random": "RANDOM",
        }

        self.library_selection_mapping = {
            "poly-dT": "Oligo-dT",
            "random": "RANDOM",
        }

        self.instrument_model = {
            "Illumina Genome Analyzer": "ILLUMINA",
            "Illumina Genome Analyzer II": "ILLUMINA",
            "Illumina Genome Analyzer IIx": "ILLUMINA",
            "Illumina HiSeq 2500": "ILLUMINA",
            "Illumina HiSeq 2000": "ILLUMINA",
            "Illumina HiSeq 1500": "ILLUMINA",
            "Illumina HiSeq 1000": "ILLUMINA",
            "Illumina MiSeq": "ILLUMINA",
            "Illumina HiScanSQ": "ILLUMINA",
            "HiSeq X Ten": "ILLUMINA",
            "NextSeq 500": "ILLUMINA",
            "HiSeq X Five": "ILLUMINA",
            "Illumina HiSeq 3000": "ILLUMINA",
            "Illumina HiSeq 4000": "ILLUMINA",
            "NextSeq 550": "ILLUMINA"
        }

        self.field_mapping = {
            "process__uuid__uuid": "alias",
            "sequencing_protocol__content__protocol_core__protocol_name": "title",
            "sequencing_protocol__content__protocol_core__protocol_description": "description"
        }

    def _build_output(self, extracted_data, flattened_hca_data):
        extracted_data["studyRef"] = {}
        extracted_data["sampleUses"] = []

        if not extracted_data.get("attributes"):
            extracted_data["attributes"] = {}
        extracted_data["attributes"]["library_strategy"] = [dict(value="Other")]
        extracted_data["attributes"]["library_source"] = [dict(value="TRANSCRIPTOMIC SINGLE CELL")]

        primer = flattened_hca_data.get("library_preparation_protocol__content__primer")
        if primer:
            extracted_data["attributes"]["library_selection"] = [dict(value=self.library_selection_mapping.get(primer, ""))]

        paired_end = flattened_hca_data.get("sequencing_protocol__content__paired_end")
        if paired_end:
            extracted_data["attributes"]["library_layout"] = [dict(value="PAIRED")]
            extracted_data["attributes"]["nominal_length"] = [dict(value="")]
            extracted_data["attributes"]["nominal_sdev"] = [dict(value="")]
        else:
            extracted_data["attributes"]["library_layout"] = [dict(value="SINGLE")]

        instr_model = flattened_hca_data.get("sequencing_protocol__content__instrument_manufacturer_model__text")
        if instr_model:
            extracted_data["attributes"]["instrument_model"] = [dict(value=instr_model)]
            extracted_data["attributes"]["platform_type"] = [dict(value=self.instrument_model.get(instr_model, ""))]

        extracted_data["attributes"]["design_description"] = [dict(value="")]
        extracted_data["attributes"]["library_name"] = [dict(value=extracted_data.get("cell_suspension__biomaterial_core__biomaterial_id", ""))]

        return extracted_data

    def _build_output(self, extracted_data, flattened_hca_data):
        extracted_data["studyRef"] = {}
        extracted_data["sampleUses"] = []

        if not extracted_data.get("attributes"):
            extracted_data["attributes"] = {}
        extracted_data["attributes"]["library_strategy"] = [dict(value="Other")]
        extracted_data["attributes"]["library_source"] = [dict(value="TRANSCRIPTOMIC SINGLE CELL")]

        primer = flattened_hca_data.get("library_preparation_protocol__content__primer")
        if primer:
            extracted_data["attributes"]["library_selection"] = [dict(value=self.library_selection_mapping.get(primer, ""))]

        paired_end = flattened_hca_data.get("sequencing_protocol__content__paired_end")
        if paired_end:
            extracted_data["attributes"]["library_layout"] = [dict(value="PAIRED")]
            extracted_data["attributes"]["nominal_length"] = [dict(value="")]
            extracted_data["attributes"]["nominal_sdev"] = [dict(value="")]
        else:
            extracted_data["attributes"]["library_layout"] = [dict(value="SINGLE")]

        instr_model = flattened_hca_data.get("sequencing_protocol__content__instrument_manufacturer_model__text")
        if instr_model:
            extracted_data["attributes"]["instrument_model"] = [dict(value=instr_model)]
            extracted_data["attributes"]["platform_type"] = [dict(value=self.instrument_model.get(instr_model, ""))]

        extracted_data["attributes"]["design_description"] = [dict(value="")]
        extracted_data["attributes"]["library_name"] = [dict(value=extracted_data.get("cell_suspension__biomaterial_core__biomaterial_id", ""))]

        self._buid_links(extracted_data, {})

        return extracted_data

    # TODO implement
    def _buid_links(self, extracted_data, links):
        extracted_data["studyRef"] = {"alias": "{studyAlias.placeholder}"}
        extracted_data["sampleUses"] = [{"sampleRef": {"alias": "{sampleAlias.placeholder}"}}]

