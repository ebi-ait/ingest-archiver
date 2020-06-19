from collections import namedtuple

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


Synonym = namedtuple('Synonym', ['main', 'alternate'])


def _prepare_map():
    model_names = ['Illumina Genome Analyzer', 'Illumina Genome Analyzer II', 'Illumina Genome Analyzer IIx',
                   'Illumina HiSeq 2500', 'Illumina HiSeq 2000', 'Illumina HiSeq 1500', 'Illumina HiSeq 1000',
                   'Illumina MiSeq', 'Illumina HiScanSQ', 'HiSeq X Ten', 'NextSeq 500', 'HiSeq X Five',
                   'Illumina HiSeq 3000', 'Illumina HiSeq 4000', 'NextSeq 550']
    instrument_models = [illumina(name) for name in model_names]
    model_map = {model.hca_name: model for model in instrument_models}

    synonyms = [Synonym('hiseq x ten', 'illumina hiseq x 10'), Synonym('nextseq 500', 'illumina nextseq 500')]
    for synonym in synonyms:
        model_map[synonym.alternate] = model_map[synonym.main].hca_synonym(synonym.alternate)

    return model_map


__instrument_model_map__ = _prepare_map()


def to_dsp_name(hca_name: str):
    instrument_model = __instrument_model_map__.get(hca_name.lower())
    return instrument_model.dsp_name if instrument_model else 'unspecified'