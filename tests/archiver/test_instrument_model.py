from unittest import TestCase

from archiver.instrument_model import illumina


class InstrumentModelTest(TestCase):

    def test_illumina_instrument_model(self):
        # given:
        genome_analyzer = illumina('Illumina Genome Analyzer II')

        # expect:
        self.assertEqual('illumina genome analyzer ii', genome_analyzer.hca_name)
        self.assertEqual('Illumina Genome Analyzer II', genome_analyzer.dsp_name)
        self.assertEqual('ILLUMINA', genome_analyzer.platform_type)

    def test_create_hca_synonym(self):
        # given:
        hiseq_x_ten = illumina('HiSeq X Ten')
        self.assertEqual('hiseq x ten', hiseq_x_ten.hca_name)

        # when:
        synonym = hiseq_x_ten.hca_synonym('illumina hiseq x 10')

        # then:
        self.assertIsNotNone(synonym)
