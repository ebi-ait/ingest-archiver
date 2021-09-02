import time
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

    def prepare_sequencing_runs(self, manifest_id: str, md5_file: str, ftp_parent_dir: str = '', action: str = 'ADD'):
        manifest = self.get_manifest(manifest_id)
        assay_process = manifest.get_assay_process()
        assay_process_uuid = assay_process['uuid']['uuid']
        md5 = self.load_md5_file(md5_file)
        manifest_files = list(manifest.get_files())
        files = [self._get_file_info(file, md5, ftp_parent_dir) for file in manifest_files]
        files_by_lane_index = self._group_files_by_lane_index(files)
        timestamp = time.strftime("%Y%m%d-%H%M%S")

        runs = []
        for lane_index, lane_files in files_by_lane_index.items():
            alias = f'{timestamp}_sequencingRun_{assay_process_uuid}_{lane_index}'
            run = self._create_run_data(alias, action, assay_process, lane_files)
            runs.append(run)

        return runs

    def _create_run_data(self, alias, action, assay_process, lane_files):
        run_data = {
            'experiment_accession': self._get_experiment_accession(assay_process),
            'files': lane_files
        }

        accession = lane_files[0].get('accession') if lane_files else None

        if action.upper() == 'ADD':
            if accession:
                raise Error(f'The sequencing run {alias} should have no run accession {accession}.')

            run_data['run_alias'] = alias
            run_data['run_title'] = alias

        if action.upper() == 'MODIFY':
            if not accession:
                raise Error(f'The sequencing run {alias} should have a run accession')

            run_data['run_accession'] = accession

        return run_data

    def _group_files_by_lane_index(self, files):
        lanes = {}
        for file in files:
            lane_index = file.get('lane_index')
            if lane_index not in lanes:
                lanes[lane_index] = []
            lanes[lane_index].append(file)
        return lanes

    def _get_experiment_accession(self, assay_process: dict):
        assay_content = assay_process.get('content', {})
        insdc_experiment = assay_content.get('insdc_experiment', {})
        experiment_accession = insdc_experiment.get('insdc_experiment_accession')
        if not experiment_accession:
            assay_process_uuid = assay_process['uuid']['uuid']
            raise Error(f'The sequencing experiment accession for assay process {assay_process_uuid} is missing.')
        return experiment_accession

    def _get_file_info(self, manifest_file, md5, ftp_parent_dir=''):
        filename = manifest_file.get('fileName')
        file_location = filename
        if ftp_parent_dir:
            file_location = f'{ftp_parent_dir}/{filename}'

        checksum = self._get_checksum(filename, md5)
        read_index = manifest_file['content']['read_index']
        lane_index = manifest_file['content']['lane_index']

        file = {
            'url': manifest_file['_links']['self']['href'],
            'uuid': manifest_file['uuid']['uuid'],
            'filename': file_location,
            'filetype': 'fastq',
            'checksum_method': 'MD5',
            'checksum': checksum,
            'read_types': READ_TYPES.get(read_index),
            'lane_index': lane_index
        }

        file_content = manifest_file.get('content', {})
        run_accessions = file_content.get('insdc_run_accessions', [])
        if run_accessions:
            file['accession'] = run_accessions[0]

        return file

    def _get_checksum(self, filename, md5):
        checksum = md5.get(filename)
        if not checksum:
            raise Error(f'There is no checksum found for {filename}')
        return checksum

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
