# 1. fix submission to delete the project and seq experiments should point to correct ENA study accession
# 2. submit samples and sequencing experiment, keep track of accessions - study, sample, seq experiment
# 3. upload to ftp for each file - submission-uuid/files
# generate sequencing run entities - dunno how yet
# using file upload plan
# for each sequencing run
# assign read type for each file
# create run xml - wait to be validated and wait for accessions
# create submission xml
# https://ena-docs.readthedocs.io/en/latest/submit/reads/programmatic.html
# curl -u username:password -F "SUBMISSION=@submission.xml" -F "EXPERIMENT=@experiment.xml" -F "RUN=@run.xml" "https://wwwdev.ebi.ac.uk/ena/submit/drop-box/submit/"

import xml.etree.ElementTree as ET


class RunXmLConverter:
    def __init__(self):
        pass

    def convert_to_xml_tree(self, data) -> ET.ElementTree:
        run_set = ET.Element("RUN_SET")
        run = ET.SubElement(run_set, "RUN")
        run.set('alias', data.get('run_alias'))

        title = ET.SubElement(run, "TITLE")
        title.text = data.get('run_title')

        experiment_ref = ET.SubElement(run, "EXPERIMENT_REF")
        experiment_ref.set('refname', data.get('experiment_ref'))

        data_block = ET.SubElement(run, "DATA_BLOCK")

        files = ET.SubElement(data_block, "FILES")

        for file in data.get('files'):
            file_elem = ET.SubElement(files, "FILE")
            file_elem.set('filename', file.get('filename'))
            file_elem.set('filetype', file.get('filetype'))
            file_elem.set('checksum_method', file.get('checksum_method'))
            file_elem.set('checksum', file.get('checksum'))

            for read_type in file.get('read_types'):
                file_elem_read_type = ET.SubElement(file_elem, "READ_TYPE")
                file_elem_read_type.text = read_type

        run_xml_tree = ET.ElementTree(run_set)
        return run_xml_tree