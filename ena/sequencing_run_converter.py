import xml.etree.ElementTree as ET

from api.ingest import IngestAPI
from archiver.archiver import Manifest

# TODO This is only applicable for Peng's dataset
READ_TYPES = {
    'index1': ['sample_barcode'],
    'read1': [
        'cell_barcode',
        'umi_barcode'
    ],
    'read2': [
        'single'
    ]
}


class SequencingRunConverter:
    def __init__(self, ingest_api: IngestAPI):
        self.ingest_api = ingest_api

    def convert_sequencing_run_data_to_xml_tree(self, run_data: dict) -> ET.ElementTree:
        run_set = ET.Element("RUN_SET")
        run = ET.SubElement(run_set, "RUN")
        run.set('alias', run_data.get('run_alias'))

        title = ET.SubElement(run, "TITLE")
        title.text = run_data.get('run_title')

        experiment_ref = ET.SubElement(run, "EXPERIMENT_REF")
        experiment_ref.set('accession', run_data.get('experiment_accession'))

        data_block = ET.SubElement(run, "DATA_BLOCK")

        files = ET.SubElement(data_block, "FILES")

        for file in run_data.get('files'):
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

    def get_manifest(self, manifest_id: str):
        manifest = Manifest(self.ingest_api, manifest_id)
        return manifest

    def prepare_sequencing_run_data(self, manifest_id: str, md5_file: str, no_dir=False):
        data = {}
        manifest = self.get_manifest(manifest_id)
        submission_uuid = manifest.get_submission_uuid()
        assay_process = manifest.get_assay_process()
        experiment_accession = assay_process['content']['insdc_experiment']['insdc_experiment_accession']
        assay_process_uuid = assay_process['uuid']['uuid']

        run_alias = f'sequencingRun-{assay_process_uuid}'
        data['run_alias'] = run_alias
        data['run_title'] = run_alias
        data['experiment_accession'] = experiment_accession
        data['files'] = []

        md5 = self.load_md5_file(md5_file)

        files = list(manifest.get_files())
        for manifest_file in files:
            read_index = manifest_file['content']['read_index']
            lane_index = manifest_file['content']['lane_index']
            filename = manifest_file.get('fileName')

            # The files will be uploaded to the submission uuid directory in the FTP upload area
            if no_dir:
                file_location = filename
            else:
                file_location = f'{submission_uuid}/{filename}'

            file = {
                'filename': file_location,
                'filetype': 'fastq',
                'checksum_method': 'MD5',
                'checksum': md5.get(filename),
                'read_types': READ_TYPES.get(read_index),
                'lane_index': lane_index
            }

            data['files'].append(file)

        return data

    def load_md5_file(self, md5_file: str):
        md5 = {}
        with open(md5_file) as f:
            lines = [line.rstrip() for line in f]

        for line in lines:
            parts = line.split('  ')
            checksum = parts[0]
            filename = parts[1]
            md5[filename] = checksum

        return md5
