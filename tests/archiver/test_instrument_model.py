from unittest import TestCase

from archiver.dsp.converter.ena_experiment import InstrumentModel


class InstrumentModelTest(TestCase):

    def test_illumina_instrument_model(self):
        # given:
        genome_analyzer = InstrumentModel.illumina('Illumina Genome Analyzer II')

        # expect:
        self.assertEqual('illumina genome analyzer ii', genome_analyzer.hca_name)
        self.assertEqual('Illumina Genome Analyzer II', genome_analyzer.dsp_name)
        self.assertEqual('ILLUMINA', genome_analyzer.platform_type)

    def test_create_hca_synonym(self):
        # given:
        hiseq_x_ten = InstrumentModel.illumina('HiSeq X Ten')
        self.assertEqual('hiseq x ten', hiseq_x_ten.hca_name)

        # when:
        synonym = hiseq_x_ten.hca_synonym('illumina hiseq x 10')

        # then:
        self.assertEqual('illumina hiseq x 10', synonym.hca_name)
        self.assertEqual('HiSeq X Ten', synonym.dsp_name)
        self.assertEqual('ILLUMINA', synonym.platform_type)
