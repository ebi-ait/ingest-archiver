import logging
from flatten_json import flatten

HCA_USI_KEY_MAP = {
    "uuid__uuid": "alias",
    "content__name": "title",
    "content__ncbi_taxon_id": "taxonId",
    "submissionDate": "releaseDate"
}


class ConversionError(Exception):
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message


class Converter:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def convert_sample(self, hca_data):
        try:
            extracted_data = self._extract_sample_fields(hca_data)
            converted_data = self._build_output(extracted_data)
        except KeyError as e:
            error_message = "Error:" + str(e)
            self.logger.error(error_message)
            raise ConversionError("Conversion Error",
                                  "An error occurred in converting the metadata. Data maybe malformed.")
        return converted_data

    def _extract_sample_fields(self, hca_data):
        flattened_hca_data = flatten(hca_data, '__')

        extracted_data = {"attributes": self._extract_attributes(flattened_hca_data)}

        for key, new_key in HCA_USI_KEY_MAP.items():
            if key in flattened_hca_data:
                extracted_data[new_key] = flattened_hca_data[key]
            else:
                self.logger.warning(key + ' is not found in the metadata.')

        return extracted_data

    def _extract_attributes(self, flattened_hca_data):
        attributes = {}
        prefix = "content__"
        for key, value in flattened_hca_data.items():
            if key.startswith(prefix) and key not in HCA_USI_KEY_MAP:
                attr = {
                    "name": key.replace(prefix, ""),
                    "value": value,
                    "terms": []
                }
                attributes[attr['name']] = [dict(value=value)]
        return attributes

    def _build_output(self, extracted_data):
        usi_data = {
            "alias": extracted_data["alias"],
            "team": {
                "name": 'self.hca-user'
            },
            "description": "",
            "attributes": extracted_data["attributes"],
            "releaseDate": extracted_data["releaseDate"].split('T')[0],  # extract date from 2017-09-28T10:52:59.419Z
            "sampleRelationships": [],
            "taxonId": extracted_data["taxonId"]
        }

        # non required fields
        if "title" in extracted_data:
            usi_data["title"] = extracted_data["title"]

        return usi_data
