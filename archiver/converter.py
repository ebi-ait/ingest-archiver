from flatten_json import flatten

HCA_USI_KEY_MAP = {
    "uuid_uuid": "alias",
    "content_id": "title",
    "content_species_ontology": "taxonId",
    "content_species_text": "taxon",
    "submissionDate": "releaseDate"
}


class ConversionError(Exception):
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message


class Converter:
    def convert_sample(self, hca_data):
        try:
            extracted_data = self._extract_sample_fields(hca_data)
            converted_data = self._build_output(extracted_data)
        except KeyError:
            raise ConversionError("Conversion Error",
                                  "An error occured in converting the metadata. Data maybe malformed.")

        return converted_data

    def _extract_sample_fields(self, hca_data):
        flattened_hca_data = flatten(hca_data)

        extracted_data = {"attributes": self._extract_attributes(flattened_hca_data)}

        for key, new_key in HCA_USI_KEY_MAP.items():
            if key in flattened_hca_data:
                extracted_data[new_key] = flattened_hca_data[key]

        return extracted_data

    def _extract_attributes(self, flattened_hca_data):
        attributes = []
        prefix = "content_"
        for key, value in flattened_hca_data.items():
            if key.startswith(prefix) and key not in HCA_USI_KEY_MAP:
                attr = {
                    "name": key.replace(prefix, ""),
                    "value": value,
                    "terms": []
                }
                attributes.append(attr)

        return attributes

    def _build_output(self, extracted_data):
        # TODO refer to the metadata schema, currently based on v3
        usi_data = {
            "alias": extracted_data["alias"],
            # "alias": 'hca' + str(randint(0, 1000)),
            "team": {
                "name": 'self.hca-user'
            },
            'title': extracted_data["title"],
            "description": "",
            "attributes": extracted_data["attributes"],
            "releaseDate": extracted_data["releaseDate"].split('T')[0],  # extract date from 2017-09-28T10:52:59.419Z
            "sampleRelationships": [],
            "taxonId": extracted_data["taxonId"],
            "taxon": extracted_data["taxon"]  # TODO in v4 there is a field ncbi_taxon_id
        }
        return usi_data
