import unittest
import time
import os
import tempfile
import hashlib
from ftplib import FTP
from config import ENA_FTP_HOST, ENA_WEBIN_USERNAME, ENA_WEBIN_PASSWORD

class TestSubmitExperiment(unittest.TestCase):

    def setUp(self):
        self.ftp = FTP(ENA_FTP_HOST, ENA_WEBIN_USERNAME, ENA_WEBIN_PASSWORD)
        self.run_file_1, self.md5_1 = TestSubmitExperiment.get_test_file_and_hash()
        self.run_file_2, self.md5_2 = TestSubmitExperiment.get_test_file_and_hash()
        print(self.run_file_1.name)
        print(self.run_file_2.name)
        self.ftp.storbinary(f'STOR {os.path.basename(self.run_file_1.name)}', self.run_file_1, 1024)
        self.ftp.storbinary(f'STOR {os.path.basename(self.run_file_2.name)}', self.run_file_2, 1024)
        super().setUp()

    def test_submit_experiment(self):
        # create xml

        project_ref = f"project_{time.time()}"
        sample_ref = f"{project_ref}_sample_1"
        experiment_ref = f"{project_ref}_seq_protocol_1"
        run_ref = f"{project_ref}_run_1"

        study = TestSubmitExperiment.dummy_study_xml(project_ref)
        sample = TestSubmitExperiment.dummy_sample_xml(sample_ref)
        experiment = TestSubmitExperiment.dummy_experiment_xml(experiment_ref, sample_ref, project_ref)
        run = TestSubmitExperiment.dummy_run_xml(run_ref, experiment_ref, {'name': os.path.basename(self.run_file_1.name), 'md5': self.md5_1}, {'name': os.path.basename(self.run_file_2.name), 'md5': self.md5_2})

        print(study)
        print(sample)
        print(experiment)
        print(run)

        # submit
        # process receipt
        # check ingest accession?


    def tearDown(self):
        try:
            self.ftp.delete(os.path.basename(self.run_file_1.name))
            self.ftp.delete(os.path.basename(self.run_file_2.name))
            self.ftp.close()
        except Exception:
            pass

    @staticmethod
    def get_test_file_and_hash():
        test_file = tempfile.NamedTemporaryFile()
        test_file.write(os.urandom(1024))

        hash_md5 = hashlib.md5()
        for chunk in iter(lambda: test_file.read(1024), b""):
            hash_md5.update(chunk)

        return test_file, hash_md5.hexdigest()


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
    def dummy_run_xml(alias, experiment_ref, file1, file2):
        return f"""<RUN alias="{alias}">
  <TITLE>Test run</TITLE>
  <EXPERIMENT_REF refname="{experiment_ref}"/>
  <DATA_BLOCK>
    <FILES>
      <FILE filename="{file1['name']}" filetype="fastq" checksum_method="MD5" checksum="{file1['md5']}"/>
      <FILE filename="{file2['name']}" filetype="fastq" checksum_method="MD5" checksum="{file2['md5']}"/>
    </FILES>
  </DATA_BLOCK>
</RUN>
            """
