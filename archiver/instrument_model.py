PLATFORM_TYPE_ILLUMINA = 'ILLUMINA'


class InstrumentModel:

    def __init__(self, hca_name: str = '', platform_type: str = '', dsp_name: str = ''):
        self.hca_name = hca_name
        self.platform_type = platform_type
        self.dsp_name = dsp_name

    def hca_synonym(self, hca_name: str):
        return InstrumentModel(hca_name, self.platform_type, self.dsp_name)


def illumina(dsp_name: str) -> InstrumentModel:
    return InstrumentModel(dsp_name.lower(), PLATFORM_TYPE_ILLUMINA, dsp_name)


instrument_model_map = {
    "illumina genome analyzer": {
        "platform_type": "ILLUMINA",
        "intrument_model": "Illumina Genome Analyzer"
    },
    "illumina genome analyzer ii": {
        "platform_type": "ILLUMINA",
        "intrument_model": "Illumina Genome Analyzer II"
    },
    "illumina genome analyzer iix": {
        "platform_type": "ILLUMINA",
        "intrument_model": "Illumina Genome Analyzer IIx"
    },
    "illumina hiseq 2500": {
        "platform_type": "ILLUMINA",
        "intrument_model": "Illumina HiSeq 2500"
    },
    "illumina hiseq 2000": {
        "platform_type": "ILLUMINA",
        "intrument_model": "Illumina HiSeq 2000"
    },
    "illumina hiseq 1500": {
        "platform_type": "ILLUMINA",
        "intrument_model": "Illumina HiSeq 1500"
    },
    "illumina hiseq 1000": {
        "platform_type": "ILLUMINA",
        "intrument_model": "Illumina HiSeq 1000"
    },
    "illumina miseq": {
        "platform_type": "ILLUMINA",
        "intrument_model": "Illumina MiSeq"
    },
    "illumina hiscansq": {
        "platform_type": "ILLUMINA",
        "intrument_model": "Illumina HiScanSQ"
    },
    "hiseq x ten": {
        "platform_type": "ILLUMINA",
        "intrument_model": "HiSeq X Ten",
        "synonymns": [
            "illumina hiseq x 10"
        ]
    },
    "nextseq 500": {
        "platform_type": "ILLUMINA",
        "intrument_model": "NextSeq 500",
        "synonymns": [
            "illumina nextseq 500"
        ]
    },
    "hiseq x five": {
        "platform_type": "ILLUMINA",
        "intrument_model": "HiSeq X Five",
    },
    "illumina hiseq 3000": {
        "platform_type": "ILLUMINA",
        "intrument_model": "Illumina HiSeq 3000"
    },
    "illumina hiseq 4000": {
        "platform_type": "ILLUMINA",
        "intrument_model": "Illumina HiSeq 4000"
    },
    "nextseq 550": {
        "platform_type": "ILLUMINA",
        "intrument_model": "NextSeq 550",
    }
}
