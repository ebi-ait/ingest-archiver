import json
import unittest
from os.path import dirname

from biosamples_v4.models import Sample, Attribute
from typing import List

from converter.biosample import BioSamplesConverter


class MyTestCase(unittest.TestCase):

    def setUp(self) -> None:
        with open(dirname(__file__) + '/../resources/biomaterials.json') as file:
            self.biomaterials = json.load(file)

        self.biosamples_converter = BioSamplesConverter()
        self.domain = 'self.test_domain'

    def test_given_ingest_biomaterial_when_release_date_defined_in_project_converts_correct_biosample(self):
        biomaterial = self.__get_biomaterial_by_index(0)

        release_date = '2020-08-01T14:26:37.998Z'
        biosample = self.__create_a_sample(release_date)

        converted_bio_sample = self.biosamples_converter.convert(biomaterial, self.domain, release_date)

        self.assertEqual(SampleMatcher(biosample), converted_bio_sample)

    def test_given_ingest_biomaterial_when_release_date_NOT_defined_in_project_converts_correct_biosample(self):
        biomaterial = self.__get_biomaterial_by_index(0)

        submission_date = '2019-07-18T21:12:39.770Z'
        biosample = self.__create_a_sample(submission_date)

        converted_bio_sample = self.biosamples_converter.convert(biomaterial, self.domain,)

        self.assertEqual(SampleMatcher(biosample), converted_bio_sample)

    def __create_a_sample(self, date):
        biosample = Sample(
            accession='SAMEA6877932',
            name='Bone Marrow CD34+ stem/progenitor cells',
            release=date,
            update='2020-06-12T14:26:37.998Z',
            domain=self.domain,
            species='Homo sapiens',
            ncbi_taxon_id=9606,
        )
        biosample._append_organism_attribute()
        self.__create_attributes(biosample,
            {
             'Biomaterial Core - Biomaterial Id': 'HS_BM_2_cell_line',
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
        return list(self.biomaterials['biomaterials'].values())[index]

    @staticmethod
    def __create_attributes(biosample:Sample, attributes:dict):
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
