import unittest

from config import ENA_FTP_DIR
from hca.assay import AssayData
from converter.ena.classes import FileFiletype
from converter.ena.ena_run import EnaRun
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig


class TestEnaRun(unittest.TestCase):
    serializer = XmlSerializer(config=SerializerConfig(pretty_print=True))

    def test_valid_run(self):
        assay_data = EnaRunTestData.test_assay_data()
        run = EnaRun(EnaRunTestData.protocol_id).create(assay_data.assays[0])
        generated_xml = self.serializer.render(run)

        self.assertEqual(generated_xml, EnaRunTestData.xml())


    def test_invalid_run_keyerror(self):
        assay_data = EnaRunTestData.test_assay_data()
        del assay_data.assays[0]["sequencing_protocol"]

        with self.assertRaises(KeyError):
            EnaRun(EnaRunTestData.protocol_id).create(assay_data.assays[0])


class EnaRunTestData:
    sub_uuid = "sub_uuid"
    process_id = "process_id"
    process_uuid = "process_uuid"
    protocol_id = "seq_protocol_1_id"
    protocol_desc = "seq_protocol_1 desc"
    file_name_1 = "file1.fq"
    file_format_1 = "fastq"
    file_md5_1 = "md5_1"
    file_name_2 = "file2.fq"
    file_format_2 = "fq"
    file_md5_2 = "md5_2"

    @staticmethod
    def test_assay_data():
        assay_data = AssayData(None, EnaRunTestData.sub_uuid)
        assay_data.assays = [
            {"content": {"process_core": {"process_id": EnaRunTestData.process_id}},
             "uuid": {"uuid": EnaRunTestData.process_uuid},
             "sequencing_protocol": {
                 "content":
                     {
                         "protocol_core": {
                             "protocol_id": EnaRunTestData.protocol_id,
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
                 "fileArchiveResult": {
                     "md5": EnaRunTestData.file_md5_1,
                     "enaUploadPath": EnaRunTestData.file_name_1,
                     "error": None
                 }
             }, {
                 "content":
                     {
                         "file_core": {
                             "file_name": EnaRunTestData.file_name_2,
                             "format": EnaRunTestData.file_format_2
                         }
                     },
                 "fileArchiveResult": {
                     "md5": EnaRunTestData.file_md5_2,
                     "enaUploadPath": EnaRunTestData.file_name_2,
                     "error": None
                 }
             }
             ]
             }]
        return assay_data

    @staticmethod
    def xml():
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<RUN alias="{EnaRunTestData.protocol_id}">
  <TITLE>{EnaRunTestData.process_id}</TITLE>
  <EXPERIMENT_REF accession="{EnaRunTestData.protocol_id}"/>
  <DATA_BLOCK>
    <FILES>
      <FILE filename="{EnaRunTestData.file_name_1}" filetype="{FileFiletype.FASTQ.value}" checksum_method="MD5" checksum="{EnaRunTestData.file_md5_1}"/>
      <FILE filename="{EnaRunTestData.file_name_2}" filetype="{FileFiletype.FASTQ.value}" checksum_method="MD5" checksum="{EnaRunTestData.file_md5_2}"/>
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


