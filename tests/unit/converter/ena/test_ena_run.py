import unittest

from config import ENA_FTP_DIR
from converter.ena.classes import FileFiletype
from converter.ena.ena import HcaData
from converter.ena.ena_run import EnaRun
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig


class TestEnaRun(unittest.TestCase):
    serializer = XmlSerializer(config=SerializerConfig(pretty_print=True))

    def test_valid_run(self):
        hca_data_valid = HcaData('uuid')
        hca_data_valid.submission = EnaRunTestData.submission()

        run = EnaRun(hca_data_valid).run(hca_data_valid.submission["assays"][0])
        generated_xml = self.serializer.render(run)

        self.assertEqual(generated_xml, EnaRunTestData.xml())


    def test_invalid_run_keyerror(self):
        hca_data_no_sub_uuid = HcaData('uuid')
        hca_data_no_sub_uuid.submission = EnaRunTestData.submission()
        del hca_data_no_sub_uuid.submission["uuid"]

        with self.assertRaises(KeyError):
            EnaRun(hca_data_no_sub_uuid).run(hca_data_no_sub_uuid.submission["assays"][0])


class EnaRunTestData:
    sub_uuid = "sub_uuid"
    process_id = "process_id"
    process_uuid = "process_uuid"
    protocol_desc = "seq_protocol_1 desc"
    file_name_1 = "file1.fq"
    file_format_1 = "fastq"
    file_md5_1 = "test_md5"
    file_name_2 = "file2.fq"
    file_format_2 = "fq"
    file_md5_2 = "MISSING_MD5"

    @staticmethod
    def submission():
        return {
            "uuid" : { "uuid": EnaRunTestData.sub_uuid },
            "assays": [
            {   "content": { "process_core": { "process_id": EnaRunTestData.process_id } },
                "uuid": {"uuid": EnaRunTestData.process_uuid },
                "sequencing_protocol": {
                    "content":
                        {
                            "protocol_core": {
                                "protocol_description": EnaRunTestData.protocol_desc
                            }
                        }
                },
                "derived_files": [{
                    "content":
                        {
                            "file_core": {
                                "file_name": EnaRunTestData.file_name_1,
                                "format": EnaRunTestData.file_format_1
                            }
                        },
                    "archiveResult": { "md5" : EnaRunTestData.file_md5_1 }
                }, {
                    "content":
                        {
                            "file_core": {
                                "file_name": EnaRunTestData.file_name_2,
                                "format": EnaRunTestData.file_format_2
                            }
                        }
                }]
            }
        ]
        }

    @staticmethod
    def xml():
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<RUN alias="{EnaRunTestData.process_uuid}">
  <TITLE>{EnaRunTestData.process_id}</TITLE>
  <EXPERIMENT_REF accession=""/>
  <DATA_BLOCK>
    <FILES>
      <FILE filename="{ENA_FTP_DIR}/{EnaRunTestData.sub_uuid}/{EnaRunTestData.file_name_1}" filetype="{FileFiletype.FASTQ.value}" checksum_method="MD5" checksum="{EnaRunTestData.file_md5_1}"/>
      <FILE filename="{ENA_FTP_DIR}/{EnaRunTestData.sub_uuid}/{EnaRunTestData.file_name_2}" filetype="{FileFiletype.FASTQ.value}" checksum_method="MD5" checksum="{EnaRunTestData.file_md5_2}"/>
    </FILES>
  </DATA_BLOCK>
  <RUN_ATTRIBUTES>
    <RUN_ATTRIBUTE>
      <TAG>Description</TAG>
      <VALUE>{EnaRunTestData.protocol_desc}</VALUE>
    </RUN_ATTRIBUTE>
  </RUN_ATTRIBUTES>
</RUN>
"""
