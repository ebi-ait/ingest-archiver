def dsp_attribute(*args):
    value = args[0]
    return [{'value': value}]


def fixed_dsp_attribute(*args):
    value = args[1]
    return dsp_attribute(value)