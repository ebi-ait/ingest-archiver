def dsp_attribute(*args):
    value = args[0]
    if value is not None:
        return [{'value': value}]


def fixed_dsp_attribute(*args):
    value = args[1]
    return dsp_attribute(value)


def taxon_id(*args):
    taxon_ids = args[0]
    return taxon_ids[0] if taxon_ids and len(taxon_ids) > 0 else None


def taxon_id_attribute(*args):
    attribute_id = taxon_id(*args)
    return dsp_attribute(attribute_id)
