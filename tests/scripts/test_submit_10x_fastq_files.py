from unittest import TestCase

import xmltodict

from scripts.submit_10x_fastq_files import RunXmLConverter


class TestRunXmlConverter(TestCase):
    def setUp(self) -> None:
        self.run_xml_converter = RunXmLConverter()

    def test_convert_to_xml_tree(self):
        # TODO how can we get this info?
        # could read assay/bundle manifest
        # files will be in submission upload area directory

        run_data = {
            'run_alias': 'alias-001',
            'run_title': 'title-001',
            'experiment_ref': 'exp-ref-001',
            'files': [
                {
                    'filename': '442536_28_S12_L002_I1_001.fastq.gz',
                    'filetype': 'fastq',
                    'checksum_method': 'MD5',
                    'checksum': 'd8ca81a13acdaa9dbe62cb10c67b2b8b',
                    'read_types': [
                        'sample_barcode'
                    ]
                },
                {
                    'filename': '442536_28_S12_L002_R1_001.fastq.gz',
                    'filetype': 'fastq',
                    'checksum_method': 'MD5',
                    'checksum': 'd8ca81a13acdaa9dbe62cb10c67b2b8b',
                    'read_types': [
                        'cell_barcode',
                        'umi_barcode'
                    ]
                },
                {
                    'filename': '442536_28_S12_L002_R2_001.fastq.gz',
                    'filetype': 'fastq',
                    'checksum_method': 'MD5',
                    'checksum': 'd8ca81a13acdaa9dbe62cb10c67b2b8b',
                    'read_types': [
                        'single'
                    ]
                }
            ]
        }
        tree = self.run_xml_converter.convert_to_xml_tree(run_data)
        tree.write('actual.xml', encoding="UTF-8", xml_declaration=True)

        with open("actual.xml") as xml_file:
            actual = xmltodict.parse(xml_file.read())
            xml_file.close()

        with open("sample_run.xml") as xml_file:
            expected = xmltodict.parse(xml_file.read())
            xml_file.close()

        self.assertEqual(actual, expected)
