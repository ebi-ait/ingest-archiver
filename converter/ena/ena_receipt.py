from operator import attrgetter
from xsdata.formats.dataclass.parsers import XmlParser

from converter.ena.classes import Receipt
from converter.ena.base import XMLType, EnaArchiveException


id_getters = {
   XMLType.PROJECT: attrgetter('project'),
   XMLType.SAMPLE: attrgetter('sample'),
   XMLType.EXPERIMENT: attrgetter('experiment'),
   XMLType.RUN: attrgetter('run'),
}

class EnaReceipt:
    def __init__(self, xml_type: XMLType, input_xml, receipt_xml:str):
        self.xml_type = xml_type
        self.input_xml = input_xml
        self.receipt = XmlParser().from_string(receipt_xml, Receipt)

    def process_receipt(self):
        accessions = []
        if self.receipt.success:
            ids = id_getters[self.xml_type](self.receipt)
            for id in ids:
                # Todo: extract biosample accession for sample, instead of internal ena sample accession
                accessions.append((id.alias, id.accession))
        else:
            errors = self.get_errors()
            raise EnaArchiveException(errors)

        return accessions

    def get_errors(self):
        all_errors = self.receipt.messages.error
        return '; '.join(all_errors)



