from datetime import datetime
import json
import unittest
from os.path import dirname
from typing import List

from biosamples_v4.models import Sample, Attribute

from converter.biosamples import BioSamplesConverter
from converter.errors import MissingBioSamplesDomain, MissingBioSamplesSampleName


class BioSamplesConverterTests(unittest.TestCase):

    def setUp(self) -> None:
        with open(dirname(__file__) + '/../resources/biomaterials.json') as file:
            self.biomaterials = json.load(file)
        self.domain = 'self.test_domain'
        self.biosamples_converter = BioSamplesConverter(self.domain)

    def test_given_ingest_biomaterial_when_release_date_defined_in_project_converts_correct_biosample(
            self):
        # given
        biomaterial = self.__get_biomaterial_by_index(0)
        release_date = '2020-08-01T14:26:37.998Z'
        biosample = self.__create_a_sample(release_date=release_date)
        # when
        additional_attributes = {
            'release_date': str(release_date),
        }
        converted_bio_sample = self.biosamples_converter.convert(biomaterial, additional_attributes)
        # then
        self.assertEqual(SampleMatcher(biosample), converted_bio_sample)

    def test_given_ingest_biomaterial_when_release_date_not_defined_in_project_converts_correct_biosample(
            self):
        # given
        biomaterial = self.__get_biomaterial_by_index(0)
        biosample = self.__create_a_sample()
        # when
        converted_bio_sample = self.biosamples_converter.convert(biomaterial)
        # then
        self.assertEqual(SampleMatcher(biosample), converted_bio_sample)

    def test_when_biomaterial_has_no_name_converted_biosample_has_biomaterial_id_as_name(self):
        # given
        biomaterial = self.__get_biomaterial_by_index(1)
        biosample = self.__create_a_sample(biomaterial_id='BP37d', name='BP37d')
        # when
        converted_bio_sample = self.biosamples_converter.convert(biomaterial)
        # then
        self.assertEqual(SampleMatcher(biosample), converted_bio_sample)

    def test_sample_can_convert_sample_with_no_attributes(self):
        # given
        biomaterial = self.__get_biomaterial_by_index(0)
        target_biosample = self.__create_a_sample()
        # when
        converted_biosample = self.biosamples_converter.convert(biomaterial)
        # then
        self.assertEqual(SampleMatcher(target_biosample), converted_biosample)

    def test_sample_throws_error_with_no_domain(self):
        # given
        self.biosamples_converter = BioSamplesConverter()
        biomaterial = {}
        # then
        with self.assertRaises(MissingBioSamplesDomain):
            # when
            self.biosamples_converter.convert(biomaterial)

    def test_sample_throws_error_with_no_name(self):
        # given
        biomaterial = {}
        # then
        with self.assertRaises(MissingBioSamplesSampleName):
            # when
            self.biosamples_converter.convert(biomaterial)

    def test_sample_uses_attribute_accession(self):
        # given
        biomaterial = self.__get_biomaterial_by_id('accession-attribute-no-content-test')
        target_biosample = self.__create_a_sample()
        # when
        additional_attributes = {
            'accession': biomaterial.get('accession')
        }
        converted_biosample = self.biosamples_converter.convert(biomaterial, additional_attributes)
        # then
        self.assertEqual(SampleMatcher(target_biosample), converted_biosample)

    def test_sample_uses_attribute_accession_over_core_accession(self):
        # given
        biomaterial = self.__get_biomaterial_by_id('accession-attribute-override-test')
        target_biosample = self.__create_a_sample()
        # when
        additional_attributes = {
            'accession': biomaterial.get('accession')
        }
        converted_biosample = self.biosamples_converter.convert(biomaterial, additional_attributes)
        # then
        self.assertEqual(SampleMatcher(target_biosample), converted_biosample)

    def test_sample_uses_core_accession_if_no_attribute_accession(self):
        # given
        biomaterial = self.__get_biomaterial_by_id('accession-content-test')
        target_biosample = self.__create_a_sample()
        # when
        converted_biosample = self.biosamples_converter.convert(biomaterial)
        # then
        self.assertEqual(SampleMatcher(target_biosample), converted_biosample)

    def test_sample_does_not_need_an_accession(self):
        biomaterial = self.__get_biomaterial_by_id('accession-missing-test')
        target_biosample = self.__create_a_sample(accession=None)
        # when
        converted_biosample = self.biosamples_converter.convert(biomaterial)
        # then
        self.assertEqual(SampleMatcher(target_biosample), converted_biosample)

    def test_sample_species_from_biomaterial_when_genus_species_missing(self):
        # given
        biomaterial = self.__get_biomaterial_by_id('genus-missing-test')
        target_biosample = self.__create_a_sample(species=None)
        # when
        converted_biosample = self.biosamples_converter.convert(biomaterial)
        # then
        self.assertEqual(SampleMatcher(target_biosample), converted_biosample)

    def test_sample_species_from_biomaterial_when_genus_species_empty(self):
        # given
        biomaterial = self.__get_biomaterial_by_id('genus-empty-test')
        target_biosample = self.__create_a_sample(species=None)
        # when
        converted_biosample = self.biosamples_converter.convert(biomaterial)
        # then
        self.assertEqual(SampleMatcher(target_biosample), converted_biosample)

    def test_sample_species_from_biomaterial_when_genus_species_no_ontology(self):
        # given
        biomaterial = self.__get_biomaterial_by_id('genus-no-ontology')
        target_biosample = self.__create_a_sample(species=None)
        # when
        converted_biosample = self.biosamples_converter.convert(biomaterial)
        # then
        self.assertEqual(SampleMatcher(target_biosample), converted_biosample)

    def test_sample_ncbi_from_biomaterial_ncbi_taxon_id_missing(self):
        # given
        biomaterial = self.__get_biomaterial_by_id('ncbi-missing-test')
        target_biosample = self.__create_a_sample(ncbi_taxon_id=None)
        # when
        converted_biosample = self.biosamples_converter.convert(biomaterial)
        # then
        self.assertEqual(SampleMatcher(target_biosample), converted_biosample)

    def test_sample_ncbi_from_biomaterial_ncbi_taxon_id_empty(self):
        # given
        biomaterial = self.__get_biomaterial_by_id('ncbi-empty-test')
        target_biosample = self.__create_a_sample(ncbi_taxon_id=None)
        # when
        converted_biosample = self.biosamples_converter.convert(biomaterial)
        # then
        self.assertEqual(SampleMatcher(target_biosample), converted_biosample)

    def __create_a_sample(
            self,
            biomaterial_id='HS_BM_2_cell_line',
            accession='SAMEA6877932',
            name='Bone Marrow CD34+ stem/progenitor cells',
            release_date='2019-07-18T21:12:39.770Z',
            species='Homo sapiens',
            ncbi_taxon_id=9606
    ):
        biosample = Sample(
            accession=accession,
            name=name,
            release=datetime.strptime(release_date, '%Y-%m-%dT%H:%M:%S.%fZ'),
            update=datetime(2020, 6, 12, 14, 26, 37, 998000),
            domain=self.domain,
            species=species,
            ncbi_taxon_id=ncbi_taxon_id,
        )
        biosample._append_organism_attribute()
        self.__create_attributes(
            biosample,
            {
                'Biomaterial Core - Biomaterial Id': biomaterial_id,
                'HCA Biomaterial Type': 'cell_line',
                'HCA Biomaterial UUID': '501ba65c-0b04-430d-9aad-917935ee3c3c',
                'Is Living': 'yes',
                'Medical History - Smoking History': '20 cigarettes/day for 25 years, stopped 2000',
                'Sex': 'male',
                'project': 'Human Cell Atlas'
            }
        )
        return biosample

    def __get_biomaterial_by_index(self, index):
        return list(map(lambda attribute: attribute['attributes'], list(self.biomaterials['biomaterials'].values())))[index]

    def __get_biomaterial_by_id(self, biomaterial_id):
        return self.biomaterials.get('biomaterials', {}).get(biomaterial_id, {}).get('attributes')

    @staticmethod
    def __create_attributes(biosample: Sample, attributes: dict):
        for name, value in attributes.items():
            biosample.attributes.append(
                Attribute(
                    name=name,
                    value=value
                )
            )


class SampleMatcher:
    expected: Sample

    def __init__(self, expected):
        self.expected = expected

    def __repr__(self):
        return repr(self.expected)

    def __eq__(self, other):
        other_equals = self.expected.accession == other.accession and \
                       self.expected.name == other.name and \
                       self.expected.update == other.update and \
                       self.expected.release == other.release and \
                       self.expected.domain == other.domain and \
                       self.expected.species == other.species and \
                       self.expected.ncbi_taxon_id == other.ncbi_taxon_id
        attributes_matcher = AttributeMatcher(self.expected.attributes)
        attr_equals = attributes_matcher.__eq__(other.attributes)

        return other_equals and attr_equals


class AttributeMatcher:
    expected: List[Attribute]

    def __init__(self, expected):
        self.expected = expected

    def __repr__(self):
        return repr(self.expected)

    def __eq__(self, other):
        is_equal = True
        for index, attribute in enumerate(self.expected):
            is_equal = attribute.iris == other[index].iris and \
                       attribute.name == other[index].name and \
                       attribute.unit == other[index].unit and \
                       attribute.value == other[index].value
            if not is_equal:
                break
        return is_equal


if __name__ == '__main__':
    unittest.main()
