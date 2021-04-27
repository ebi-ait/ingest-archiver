import json
import unittest
from os.path import dirname

from biosamples_v4.models import Sample

from converter.biosample import BioSamplesConverter


class MyTestCase(unittest.TestCase):

    def setUp(self) -> None:
        with open(dirname(__file__) + '/../resources/biomaterials.json') as file:
            self.biomaterials = json.load(file)

        self.biosamples_converter = BioSamplesConverter()

    def test_given_ingest_biomaterial_when_release_date_defined_in_project_converts_correct_biosample(self):
        biomaterial = self.__get_biomaterial_by_index(0)

        release_date = '2020-08-01T14:26:37.998Z'
        biosample = Sample(
            accession='SAMEA6877932',
            name='Bone Marrow CD34+ stem/progenitor cells',
            release=release_date,
            update='2020-06-12T14:26:37.998Z',
            # domain='',
            species='Homo sapiens',
            ncbi_taxon_id=9606,
        )
        biosample._append_organism_attribute()

        converted_bio_sample = self.biosamples_converter.convert(biomaterial, release_date)

        self.assertEqual(SampleMatcher(biosample), converted_bio_sample)

    def test_given_ingest_biomaterial_when_release_date_NOT_defined_in_project_converts_correct_biosample(self):
        biomaterial = self.__get_biomaterial_by_index(0)

        submission_date = '2019-07-18T21:12:39.770Z'
        biosample = Sample(
            accession='SAMEA6877932',
            name='Bone Marrow CD34+ stem/progenitor cells',
            release=submission_date,
            update='2020-06-12T14:26:37.998Z',
            # domain='',
            species='Homo sapiens',
            ncbi_taxon_id=9606,
        )
        biosample._append_organism_attribute()

        converted_bio_sample = self.biosamples_converter.convert(biomaterial)

        self.assertEqual(SampleMatcher(biosample), converted_bio_sample)

    def __get_biomaterial_by_index(self, index):
        return list(self.biomaterials['biomaterials'].values())[index]


class SampleMatcher:
    expected: Sample

    def __init__(self, expected):
        self.expected = expected

    def __repr__(self):
        return repr(self.expected)

    def __eq__(self, other):
        return self.expected.accession == other.accession and \
               self.expected.name == other.name and \
               self.expected.update == other.update and \
               self.expected.release == other.release and \
               self.expected.species == other.species and \
               self.expected.ncbi_taxon_id == other.ncbi_taxon_id


if __name__ == '__main__':
    unittest.main()
