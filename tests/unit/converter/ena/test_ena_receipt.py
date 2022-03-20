import unittest

from converter.ena.classes import ReceiptActions
from converter.ena.base import XMLType
from converter.ena.ena_receipt import EnaReceipt


class TestEnaReceipt(unittest.TestCase):

    def test_project_receipt(self):
        ena_receipt = EnaReceipt(XMLType.STUDY, None, EnaReceiptTestData.PROJECT_RECEIPT)
        errors, accessions = ena_receipt.process_receipt()
        self.assertTrue(ena_receipt.receipt.success)
        self.assertFalse(errors)
        self.assertTrue(accessions)
        self.assertEqual(accessions[0][0], 'project_1')
        self.assertTrue((accessions[0][1]).startswith('PRJ'))

    def test_project_receipt_with_error(self):
        ena_receipt = EnaReceipt(XMLType.STUDY, None, EnaReceiptTestData.PROJECT_RECEIPT_ERROR)
        errors, accessions = ena_receipt.process_receipt()
        self.assertFalse(ena_receipt.receipt.success)
        self.assertTrue(errors)
        self.assertFalse(accessions)
        self.assertTrue("already exists" in errors[0])

    def test_sample_receipt(self):
        ena_receipt = EnaReceipt(XMLType.SAMPLE, None, EnaReceiptTestData.SAMPLE_RECEIPT)
        errors, accessions = ena_receipt.process_receipt()
        self.assertTrue(ena_receipt.receipt.success)
        self.assertFalse(errors)
        self.assertTrue(accessions)
        self.assertEqual(accessions[0][0], 'sample_1')
        self.assertTrue((accessions[0][1]).startswith('ERS'))

    def test_sample_receipt_with_error(self):
        ena_receipt = EnaReceipt(XMLType.SAMPLE, None, EnaReceiptTestData.SAMPLE_RECEIPT_ERROR)
        errors, accessions = ena_receipt.process_receipt()
        self.assertFalse(ena_receipt.receipt.success)
        self.assertTrue(errors)
        self.assertFalse(accessions)
        self.assertTrue("already exists" in errors[0])

    def test_sample_receipt_modify(self):
        ena_receipt = EnaReceipt(XMLType.SAMPLE, None, EnaReceiptTestData.SAMPLE_RECEIPT_MODIFY)
        errors, accessions = ena_receipt.process_receipt()
        self.assertTrue(ena_receipt.receipt.success)
        self.assertTrue(ena_receipt.receipt.actions)
        self.assertEqual(ena_receipt.receipt.actions[0], ReceiptActions.MODIFY)

    def test_samples_receipt(self):
        ena_receipt = EnaReceipt(XMLType.SAMPLE, None, EnaReceiptTestData.SAMPLES_RECEIPT)
        errors, accessions = ena_receipt.process_receipt()
        self.assertTrue(ena_receipt.receipt.success)
        self.assertFalse(errors)
        self.assertTrue(len(accessions) > 1)

    def test_samples_receipt_errors(self):
        ena_receipt = EnaReceipt(XMLType.SAMPLE, None, EnaReceiptTestData.SAMPLES_RECEIPT_ERROR)
        errors, accessions = ena_receipt.process_receipt()
        self.assertFalse(ena_receipt.receipt.success)
        self.assertTrue(errors)

    def test_experiment_receipt(self):
        ena_receipt = EnaReceipt(XMLType.EXPERIMENT, None, EnaReceiptTestData.EXPERIMENT_RECEIPT)
        errors, accessions = ena_receipt.process_receipt()
        self.assertTrue(ena_receipt.receipt.success)
        self.assertFalse(errors)
        self.assertEqual(accessions[0][0], 'seq_protocol_1')
        self.assertTrue((accessions[0][1]).startswith('ERX'))

    def test_experiment_receipt_error_ref_study_not_found(self):
        ena_receipt = EnaReceipt(XMLType.EXPERIMENT, None, EnaReceiptTestData.EXPERIMENT_RECEIPT_ERROR_1)
        errors, accessions = ena_receipt.process_receipt()
        self.assertFalse(ena_receipt.receipt.success)
        self.assertTrue(errors)
        self.assertFalse(accessions)
        self.assertTrue('Failed to find referenced study' in errors[0])

    def test_experiment_receipt_error_ref_sample_not_found(self):
        ena_receipt = EnaReceipt(XMLType.EXPERIMENT, None, EnaReceiptTestData.EXPERIMENT_RECEIPT_ERROR_2)
        errors, accessions = ena_receipt.process_receipt()
        self.assertFalse(ena_receipt.receipt.success)
        self.assertTrue(errors)
        self.assertFalse(accessions)
        self.assertTrue('Failed to find referenced sample' in errors[0])

    def test_experiment_receipt_error_already_exists(self):
        ena_receipt = EnaReceipt(XMLType.EXPERIMENT, None, EnaReceiptTestData.EXPERIMENT_RECEIPT_ERROR_3)
        errors, accessions = ena_receipt.process_receipt()
        self.assertFalse(ena_receipt.receipt.success)
        self.assertTrue(errors)
        self.assertFalse(accessions)
        self.assertTrue('already exists' in errors[0])


class EnaReceiptTestData:
    PROJECT_RECEIPT="""<RECEIPT receiptDate="2022-03-09T12:21:03.542Z" submissionFile="submission-USI_1646828463542.xml" success="true">
     <PROJECT accession="PRJEB51470" alias="project_1" status="PRIVATE" holdUntilDate="2024-03-09Z">
          <EXT_ID accession="ERP136097" type="study"/>
     </PROJECT>
     <SUBMISSION accession="ERA9855170" alias="SUBMISSION-09-03-2022-12:21:03:387"/>
     <MESSAGES>
          <INFO>This submission is a TEST submission and will be discarded within 24 hours</INFO>
     </MESSAGES>
     <ACTIONS>ADD</ACTIONS>
</RECEIPT>
    """
    PROJECT_RECEIPT_ERROR="""<RECEIPT receiptDate="2022-03-09T12:23:53.130Z" submissionFile="submission-USI_1646828633130.xml" success="false">
     <PROJECT alias="project_1" status="PRIVATE" holdUntilDate="2024-03-09Z"/>
     <SUBMISSION alias="SUBMISSION-09-03-2022-12:23:53:107"/>
     <MESSAGES>
          <ERROR>In project, alias:"project_1", accession:"". The object being added already exists in the submission account with accession: "PRJEB51470".</ERROR>
          <INFO>This submission is a TEST submission and will be discarded within 24 hours</INFO>
     </MESSAGES>
     <ACTIONS>ADD</ACTIONS>
</RECEIPT>
    """

    SAMPLE_RECEIPT="""<RECEIPT receiptDate="2022-03-09T12:28:34.840Z" submissionFile="submission-USI_1646828914840.xml" success="true">
     <SAMPLE accession="ERS10919639" alias="sample_1" status="PRIVATE">
          <EXT_ID accession="SAMEA9074074" type="biosample"/>
     </SAMPLE>
     <SUBMISSION accession="ERA9855171" alias="SUBMISSION-09-03-2022-12:28:34:353"/>
     <MESSAGES>
          <INFO>This submission is a TEST submission and will be discarded within 24 hours</INFO>
     </MESSAGES>
     <ACTIONS>ADD</ACTIONS>
</RECEIPT>
    """

    SAMPLE_RECEIPT_ERROR="""<RECEIPT receiptDate="2022-03-09T12:28:46.376Z" submissionFile="submission-USI_1646828926376.xml" success="false">
     <SAMPLE alias="sample_1" status="PRIVATE"/>
     <SUBMISSION alias="SUBMISSION-09-03-2022-12:28:46:303"/>
     <MESSAGES>
          <ERROR>In sample, alias:"sample_1", accession:"". The object being added already exists in the submission account with accession: "ERS10919639".</ERROR>
          <INFO>This submission is a TEST submission and will be discarded within 24 hours</INFO>
     </MESSAGES>
     <ACTIONS>ADD</ACTIONS>
</RECEIPT>
    """

    SAMPLE_RECEIPT_MODIFY="""<RECEIPT receiptDate="2022-03-09T12:29:58.440Z" submissionFile="submission-USI_1646828998440.xml" success="true">
     <SAMPLE accession="ERS10919639" alias="sample_1" status="PRIVATE">
          <EXT_ID accession="SAMEA9074074" type="biosample"/>
     </SAMPLE>
     <SUBMISSION accession="" alias="SUBMISSION-09-03-2022-12:29:58:256"/>
     <MESSAGES>
          <INFO>This submission is a TEST submission and will be discarded within 24 hours</INFO>
     </MESSAGES>
     <ACTIONS>MODIFY</ACTIONS>
</RECEIPT>
    """

    SAMPLES_RECEIPT = """<RECEIPT receiptDate="2022-03-09T20:53:07.243Z" submissionFile="submission-USI_1646859187243.xml" success="true">
         <SAMPLE accession="ERS10919677" alias="sample_3" status="PRIVATE">
              <EXT_ID accession="SAMEA9075017" type="biosample"/>
         </SAMPLE>
         <SAMPLE accession="ERS10919678" alias="sample_4" status="PRIVATE">
              <EXT_ID accession="SAMEA9075018" type="biosample"/>
         </SAMPLE>
         <SUBMISSION accession="ERA9855214" alias="SUBMISSION-09-03-2022-20:53:06:896"/>
         <MESSAGES>
              <INFO>This submission is a TEST submission and will be discarded within 24 hours</INFO>
         </MESSAGES>
         <ACTIONS>ADD</ACTIONS>
    </RECEIPT>
        """

    SAMPLES_RECEIPT_ERROR = """<RECEIPT receiptDate="2022-03-09T20:53:18.016Z" submissionFile="submission-USI_1646859198016.xml" success="false">
         <SAMPLE alias="sample_3" status="PRIVATE"/>
         <SAMPLE alias="sample_4" status="PRIVATE"/>
         <SUBMISSION alias="SUBMISSION-09-03-2022-20:53:17:951"/>
         <MESSAGES>
              <ERROR>In sample, alias:"sample_3", accession:"". The object being added already exists in the submission account with accession: "ERS10919677".</ERROR>
              <ERROR>In sample, alias:"sample_4", accession:"". The object being added already exists in the submission account with accession: "ERS10919678".</ERROR>
              <INFO>This submission is a TEST submission and will be discarded within 24 hours</INFO>
         </MESSAGES>
         <ACTIONS>ADD</ACTIONS>
    </RECEIPT>
        """

    EXPERIMENT_RECEIPT_ERROR_1 = """<RECEIPT receiptDate="2022-03-09T12:43:00.802Z" submissionFile="submission-USI_1646829780802.xml" success="false">
         <EXPERIMENT alias="seq_protocol_1" status="PRIVATE"/>
         <SUBMISSION alias="SUBMISSION-09-03-2022-12:43:00:764"/>
         <MESSAGES>
              <ERROR>In experiment, alias:"seq_protocol_1", accession:"", In reference:"STUDY_REF", reference alias:"project_x", reference accession:"". Failed to find referenced study, alias "project_x".</ERROR>
              <INFO>This submission is a TEST submission and will be discarded within 24 hours</INFO>
         </MESSAGES>
         <ACTIONS>ADD</ACTIONS>
    </RECEIPT>
        """

    EXPERIMENT_RECEIPT_ERROR_2="""<RECEIPT receiptDate="2022-03-09T12:42:23.798Z" submissionFile="submission-USI_1646829743798.xml" success="false">
     <EXPERIMENT alias="seq_protocol_1" status="PRIVATE"/>
     <SUBMISSION alias="SUBMISSION-09-03-2022-12:42:23:757"/>
     <MESSAGES>
          <ERROR>In reference:"SAMPLE_DESCRIPTOR", reference alias:"sample_x", reference accession:"". Failed to find referenced sample, alias "sample_x".</ERROR>
          <ERROR>Sample in experiment is null</ERROR>
          <INFO>This submission is a TEST submission and will be discarded within 24 hours</INFO>
     </MESSAGES>
     <ACTIONS>ADD</ACTIONS>
</RECEIPT>
    """

    EXPERIMENT_RECEIPT_ERROR_3 = """<RECEIPT receiptDate="2022-03-09T20:51:44.539Z" submissionFile="submission-USI_1646859104539.xml" success="false">
         <EXPERIMENT alias="seq_protocol_1" status="PRIVATE"/>
         <SUBMISSION alias="SUBMISSION-09-03-2022-20:51:44:505"/>
         <MESSAGES>
              <ERROR>In experiment, alias:"seq_protocol_1", accession:"". The object being added already exists in the submission account with accession: "ERX8671884".</ERROR>
              <INFO>This submission is a TEST submission and will be discarded within 24 hours</INFO>
         </MESSAGES>
         <ACTIONS>ADD</ACTIONS>
    </RECEIPT>
        """

    EXPERIMENT_RECEIPT="""<RECEIPT receiptDate="2022-03-09T12:43:13.698Z" submissionFile="submission-USI_1646829793698.xml" success="true">
     <EXPERIMENT accession="ERX8671884" alias="seq_protocol_1" status="PRIVATE"/>
     <SUBMISSION accession="ERA9855172" alias="SUBMISSION-09-03-2022-12:43:13:566"/>
     <MESSAGES>
          <INFO>This submission is a TEST submission and will be discarded within 24 hours</INFO>
     </MESSAGES>
     <ACTIONS>ADD</ACTIONS>
</RECEIPT>
    """


