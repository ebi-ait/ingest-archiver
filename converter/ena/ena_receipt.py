from xsdata.formats.dataclass.parsers import XmlParser

from converter.ena.classes import Receipt
from converter.ena.ena import XMLType


class EnaReceipt:
    def __init__(self, xml_type: XMLType, input_xml, receipt_xml:str):
        self.xml_type = xml_type
        self.input_xml = input_xml
        self.receipt = XmlParser().from_string(receipt_xml, Receipt)

    def process_receipt(self):
        errors, accessions = [], []
        if self.receipt.success:
            ids = []
            if self.xml_type == XMLType.STUDY:
                ids = self.receipt.project
            elif self.xml_type == XMLType.SAMPLE:
                ids = self.receipt.sample
            elif self.xml_type == XMLType.EXPERIMENT:
                ids = self.receipt.experiment
            elif self.xml_type == XMLType.RUN:
                ids = self.receipt.run

            for id in ids:
                # Todo: extract biosample accession for sample, instead of internal ena sample accession
                accessions.append((id.alias, id.accession))
        else:
            errors = self.get_all_errors()

        return errors, accessions

    def get_all_errors(self):
        return self.receipt.messages.error



