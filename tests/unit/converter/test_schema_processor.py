import unittest

from assertpy import assert_that

from converter.schema_processor import SchemaProcessor


class TestSchemaProcessor(unittest.TestCase):

    def setUp(self) -> None:
        self.schema_processor = SchemaProcessor()

    def test_correct_properties_extracted_from_given_schema(self):
        expected_properties = self.__get_expected_properties()
        biomaterial_schema_url = 'https://schema.humancellatlas.org/type/biomaterial/3.3.0/imaged_specimen'
        attribute_properties_from_schema = self.schema_processor.get_attributes_from_schema(
            biomaterial_schema_url)

        assert_that(attribute_properties_from_schema).is_equal_to(expected_properties)

    @staticmethod
    def __get_expected_properties():
        return [
            ['describedBy', 'string', ' version: 3.3.0'],
            ['schema_version', 'string', ' version: 3.3.0'],
            ['schema_type', 'string', ' version: 3.3.0'],
            ['provenance.describedBy', 'string', 'provenance version: 1.1.0'],
            ['provenance.schema_version', 'string', 'provenance version: 1.1.0'],
            ['provenance.schema_major_version', 'integer', 'provenance version: 1.1.0'],
            ['provenance.schema_minor_version', 'integer', 'provenance version: 1.1.0'],
            ['provenance.submission_date', 'string', 'provenance version: 1.1.0'],
            ['provenance.submitter_id', 'string', 'provenance version: 1.1.0'],
            ['provenance.update_date', 'string', 'provenance version: 1.1.0'],
            ['provenance.updater_id', 'string', 'provenance version: 1.1.0'],
            ['provenance.document_id', 'string', 'provenance version: 1.1.0'],
            ['provenance.accession', 'string', 'provenance version: 1.1.0'],
            ['biomaterial_core.describedBy', 'string', 'biomaterial_core version: 8.2.0'],
            ['biomaterial_core.schema_version', 'string', 'biomaterial_core version: 8.2.0'],
            ['biomaterial_core.biomaterial_id', 'string', 'biomaterial_core version: 8.2.0'],
            ['biomaterial_core.biomaterial_name', 'string', 'biomaterial_core version: 8.2.0'],
            ['biomaterial_core.biomaterial_description', 'string', 'biomaterial_core version: 8.2.0'],
            ['biomaterial_core.ncbi_taxon_id', 'array', 'biomaterial_core version: 8.2.0'],
            ['biomaterial_core.genotype', 'string', 'biomaterial_core version: 8.2.0'],
            ['biomaterial_core.supplementary_files', 'array', 'biomaterial_core version: 8.2.0'],
            ['biomaterial_core.biosamples_accession', 'string', 'biomaterial_core version: 8.2.0'],
            ['biomaterial_core.insdc_sample_accession', 'string', 'biomaterial_core version: 8.2.0'],
            ['biomaterial_core.HDBR_accession', 'string', 'biomaterial_core version: 8.2.0'],
            ['overview_images', 'array', ' version: 3.3.0'], ['slice_thickness', 'number', ' version: 3.3.0'],
            ['internal_anatomical_structures.describedBy', 'string', 'internal_anatomical_structures version: 5.3.5'],
            ['internal_anatomical_structures.schema_version', 'string',
             'internal_anatomical_structures version: 5.3.5'],
            ['internal_anatomical_structures.text', 'string', 'internal_anatomical_structures version: 5.3.5'],
            ['internal_anatomical_structures.ontology', 'string', 'internal_anatomical_structures version: 5.3.5'],
            ['internal_anatomical_structures.ontology_label', 'string', 'internal_anatomical_structures version: 5.3.5']
        ]


if __name__ == '__main__':
    unittest.main()
