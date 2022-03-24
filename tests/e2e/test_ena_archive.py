import unittest
import time
import io
import gzip
import uuid
import hashlib
from ftplib import FTP
from config import ENA_FTP_HOST, ENA_WEBIN_USERNAME, ENA_WEBIN_PASSWORD
from converter.ena.base import EnaModel, XMLType
from converter.ena.ena_receipt import EnaReceipt


class TestEnaArchive(unittest.TestCase):

    def setUp(self):
        self.ftp = FTP(ENA_FTP_HOST, ENA_WEBIN_USERNAME, ENA_WEBIN_PASSWORD)
        self.sub_uuid = str(uuid.uuid4())
        self.test_file_1 = EnaArchiveTestData.test_file()
        self.test_file_2 = EnaArchiveTestData.test_file()
        self.ftp.storbinary(f'STOR {self.sub_uuid}_file1.fastq.gz', self.test_file_1)
        self.ftp.storbinary(f'STOR {self.sub_uuid}_file2.fastq.gz', self.test_file_2)
        super().setUp()

    def test_submit(self):
        # create xml

        project_ref = f"{self.sub_uuid}_project"
        sample_ref = f"{self.sub_uuid}_sample"
        experiment_ref = f"{self.sub_uuid}_experiment"
        run_ref = f"{self.sub_uuid}_run"

        project_xml = EnaArchiveTestData.dummy_study_xml(project_ref)
        sample = EnaArchiveTestData.dummy_sample_xml(sample_ref)
        experiment = EnaArchiveTestData.dummy_experiment_xml(experiment_ref, sample_ref, project_ref)
        run = EnaArchiveTestData.dummy_run_xml(run_ref, experiment_ref, self.sub_uuid, self.test_file_1, self.test_file_2)

        project_receipt = EnaModel.post(XMLType.PROJECT, project_xml)
        err, acc = EnaReceipt(XMLType.PROJECT, project_xml, project_receipt).process_receipt()
        self.assertFalse(err)
        self.assertTrue(acc[0][1].startswith(EnaModel.PROJECT_ACCESSION_PREFIX))

        sample_receipt = EnaModel.post(XMLType.SAMPLE, sample)
        err, acc = EnaReceipt(XMLType.SAMPLE, sample, sample_receipt).process_receipt()
        self.assertFalse(err)
        self.assertTrue(acc[0][1].startswith(EnaModel.SAMPLE_ACCESSION_PREFIX))

        experiment_receipt = EnaModel.post(XMLType.EXPERIMENT, experiment)
        err, acc =  EnaReceipt(XMLType.EXPERIMENT, experiment, experiment_receipt).process_receipt()
        self.assertFalse(err)
        self.assertTrue(acc[0][1].startswith(EnaModel.EXPERIMENT_ACCESSION_PREFIX))

        run_receipt = EnaModel.post(XMLType.RUN, run)
        err, acc = EnaReceipt(XMLType.RUN, run, run_receipt).process_receipt()
        self.assertFalse(err)
        self.assertTrue(acc[0][1].startswith(EnaModel.RUN_ACCESSION_PREFIX))

    def tearDown(self):
        try:
            self.ftp.delete(f'{self.sub_uuid}_file1.fastq.gz')
            self.ftp.delete(f'{self.sub_uuid}_file2.fastq.gz')
            self.ftp.close()
        except Exception:
            pass


class EnaArchiveTestData:
    @staticmethod
    def test_file():
        stream = io.BytesIO()
        with gzip.open(stream, 'wb') as f:
            f.write(b"@SEQ_ID\nGATTTGGGGTTCAAAGCAGTATCGATCAAATAGTAAATCCATTTGTTCAACTCACAGTTT\n+\n!''*((((***+))%%%++)(%%%%).1***-+*''))**55CCF>>>>>>CCCCCCC65")
        stream.seek(0)
        return stream

    @staticmethod
    def file_md5(file):
        hash_md5 = hashlib.md5()
        for chunk in iter(lambda: file.read(1024), b""):
            hash_md5.update(chunk)
        return hash_md5.hexdigest()

    @staticmethod
    def dummy_study_xml(alias):
        return f"""<PROJECT_SET>
       <PROJECT alias="{alias}">
          <TITLE>Test project</TITLE>
          <DESCRIPTION>This is a test project</DESCRIPTION>
          <SUBMISSION_PROJECT>
             <SEQUENCING_PROJECT/>
          </SUBMISSION_PROJECT>
       </PROJECT>
    </PROJECT_SET>
            """

    @staticmethod
    def dummy_sample_xml(alias):
        return f"""<SAMPLE_SET>
      <SAMPLE alias="{alias}">
        <TITLE>human gastric microbiota, mucosal</TITLE>
        <SAMPLE_NAME>
          <TAXON_ID>1284369</TAXON_ID>
        </SAMPLE_NAME>
      </SAMPLE>
    </SAMPLE_SET>
            """

    @staticmethod
    def dummy_experiment_xml(alias, sample_ref, study_ref):
        return f"""<EXPERIMENT alias="{alias}">
  <TITLE>Test experiment</TITLE>
  <STUDY_REF refname="{study_ref}"/>
  <DESIGN>
    <DESIGN_DESCRIPTION/>
    <SAMPLE_DESCRIPTOR refname="{sample_ref}"/>
    <LIBRARY_DESCRIPTOR>
      <LIBRARY_NAME>Some library name</LIBRARY_NAME>
      <LIBRARY_STRATEGY>OTHER</LIBRARY_STRATEGY>
      <LIBRARY_SOURCE>TRANSCRIPTOMIC SINGLE CELL</LIBRARY_SOURCE>
      <LIBRARY_SELECTION>Oligo-dT</LIBRARY_SELECTION>
      <LIBRARY_LAYOUT>
        <PAIRED NOMINAL_LENGTH="0" NOMINAL_SDEV="0"/>
      </LIBRARY_LAYOUT>
    </LIBRARY_DESCRIPTOR>
  </DESIGN>
  <PLATFORM>
    <ILLUMINA>
      <INSTRUMENT_MODEL>Illumina NovaSeq 6000</INSTRUMENT_MODEL>
    </ILLUMINA>
  </PLATFORM>
</EXPERIMENT>
            """

    @staticmethod
    def dummy_run_xml(alias, experiment_ref, sub_uuid, test_file_1, test_file_2):
        test_file_1_md5 = EnaArchiveTestData.file_md5(test_file_1)
        test_file_2_md5 = EnaArchiveTestData.file_md5(test_file_2)
        return f"""<RUN alias="{alias}">
  <TITLE>Test run</TITLE>
  <EXPERIMENT_REF refname="{experiment_ref}"/>
  <DATA_BLOCK>
    <FILES>
      <FILE filename="{sub_uuid}_file1.fastq.gz" filetype="fastq" checksum_method="MD5" checksum="{test_file_1_md5}"/>
      <FILE filename="{sub_uuid}_file2.fastq.gz" filetype="fastq" checksum_method="MD5" checksum="{test_file_2_md5}"/>
    </FILES>
  </DATA_BLOCK>
</RUN>
            """
