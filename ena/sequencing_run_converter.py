import xml.etree.ElementTree as ET
from typing import List

from api.ingest import IngestAPI
from archiver.archiver import Manifest

# TODO This is only applicable for 10x datasets
# Add logic in checking the lib prep protocol
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

    @staticmethod
    def convert_sequencing_run_data_to_xml_tree(run_data_list: List[dict]) -> ET.ElementTree:
        run_set = ET.Element("RUN_SET")
        for run_data in run_data_list:
            run = ET.SubElement(run_set, "RUN")
            if run_data.get('run_accession'):
                run.set('accession', run_data.get('run_accession'))
            else:
                run.set('alias', run_data.get('run_alias'))

            if run_data.get('run_title'):
                title = ET.SubElement(run, "TITLE")
                title.text = run_data.get('run_title')

            experiment_ref = ET.SubElement(run, "EXPERIMENT_REF")
            experiment_ref.set('accession', run_data.get('experiment_accession'))

            data_block = ET.SubElement(run, "DATA_BLOCK")

            files = ET.SubElement(data_block, "FILES")

            SequencingRunConverter.set_files_in_data_block(files, run_data)

        run_xml_tree = ET.ElementTree(run_set)
        return run_xml_tree

    @staticmethod
    def set_files_in_data_block(files: ET.SubElement, run_data: dict):
        for file in run_data.get('files'):
            file_elem = ET.SubElement(files, "FILE")
            file_elem.set('filename', file.get('filename'))
            file_elem.set('filetype', file.get('filetype'))
            file_elem.set('checksum_method', file.get('checksum_method'))
            file_elem.set('checksum', file.get('checksum'))

            for read_type in file.get('read_types'):
                file_elem_read_type = ET.SubElement(file_elem, "READ_TYPE")
                file_elem_read_type.text = read_type

    def get_manifest(self, manifest_id: str):
        manifest = Manifest(self.ingest_api, manifest_id)
        return manifest

    def prepare_sequencing_runs(self, manifest_id: str, md5_file: str,
                                ftp_parent_dir: str = '', action: str = 'ADD'):

        manifest = self.get_manifest(manifest_id)
        assay_process = manifest.get_assay_process()
        assay_process_uuid = assay_process['uuid']['uuid']
        md5 = self.load_md5_file(md5_file)
        files = list(manifest.get_files())

        lanes = {}
        runs = []
        for manifest_file in files:
            lane_index = manifest_file.get('content').get('lane_index', 1)
            if lane_index not in lanes:
                lanes[lane_index] = []
            lanes[lane_index].append(manifest_file)

        for lane_index in lanes.keys():
            lane_files = lanes.get(lane_index)

            data = {
                'experiment_accession': self._get_experiment_accession(assay_process),
                'files': []
            }

            for manifest_file in lane_files:
                file = self._get_file_info(manifest_file, md5, ftp_parent_dir)
                data['files'].append(file)
                if manifest_file.get('content', {}).get('insdc_run_accessions', []):
                    data['run_accession'] = manifest_file['content']['insdc_run_accessions'][0]

                if action.upper() == 'ADD':
                    # TODO Change run alias to have HCA_ prefix
                    run_alias = f'sequencingRun_{assay_process_uuid}_{lane_index}'
                    data['run_alias'] = run_alias
                    data['run_title'] = run_alias

                    if data.get('run_accession'):
                        raise Error(
                            f'The sequencing run data from manifest id {manifest_id} with lane index {lane_index}'
                            f'should have no accession if action is ADD')

                if action.upper() == 'MODIFY' and not data.get('run_accession'):
                    raise Error(f'The sequencing run data from manifest id {manifest_id} with lane index {lane_index}'
                                f'should have accession if action is MODIFY')

            runs.append(data)

        return runs

    def _get_experiment_accession(self, assay_process: dict):
        experiment_accession = assay_process['content'].get('insdc_experiment', {}).get('insdc_experiment_accession')
        if not experiment_accession:
            assay_process_uuid = assay_process['uuid']['uuid']
            raise Error(f'The sequencing experiment accession for assay process {assay_process_uuid} is missing.')
        return experiment_accession

    def _get_file_info(self, manifest_file, md5, ftp_parent_dir=''):
        filename = manifest_file.get('fileName')
        file_location = filename
        if ftp_parent_dir:
            file_location = f'{ftp_parent_dir}/{filename}'

        checksum = md5.get(filename)

        if not checksum:
            raise Error(f'There is no checksum found for {filename}')

        read_index = manifest_file['content']['read_index']
        lane_index = manifest_file['content']['lane_index']
        file = {
            'filename': file_location,
            'filetype': 'fastq',
            'checksum_method': 'MD5',
            'checksum': checksum,
            'read_types': READ_TYPES.get(read_index),
            'lane_index': lane_index
        }
        return file

    @staticmethod
    def load_md5_file(md5_file: str):
        md5 = {}
        with open(md5_file) as f:
            lines = [line.rstrip() for line in f]

        for line in lines:
            parts = line.split('  ')
            checksum = parts[0]
            filename = parts[1]
            md5[filename] = checksum

        return md5


class Error(Exception):
    """Base-class for all exceptions raised by this module."""
