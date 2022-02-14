class AccessionMapper:
    mapping: [str]
    type: str

    def __init__(self, mapping: [str], accession_type: str):
        self.mapping = mapping
        self.type = accession_type
