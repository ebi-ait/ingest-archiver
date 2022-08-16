class ConversionError(ValueError):
    pass


class BioSamplesConversionError(ConversionError):
    pass


class MissingBioSamplesDomain(BioSamplesConversionError):
    def __init__(self):
        self.message = 'A BioSamples domain must be specified.'


class MissingBioSamplesSampleName(BioSamplesConversionError):
    def __init__(self):
        self.message = 'A BioSamples sample must specify a name.'
