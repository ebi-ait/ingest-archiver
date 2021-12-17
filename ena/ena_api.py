import logging
import os
import tempfile
import time
import xml.etree.ElementTree as ET
from typing import List

import requests

from api.ingest import IngestAPI
from ena.sequencing_run_converter import SequencingRunConverter
from ena.util import write_xml, load_xml_tree_from_string, xml_to_string, load_xml_dict_from_string, write_json

SUBMIT_ACTIONS = ['ADD', 'MODIFY']


class EnaApi:
    def __init__(self, ingest_api: IngestAPI, url: str = None):
        self.url = url or os.environ.get('ENA_WEBIN_API_URL')
        self.user = os.environ.get('ENA_USER')
        self.password = os.environ.get('ENA_PASSWORD')

        self.temp_dir = tempfile.TemporaryDirectory()
        self.xml_dir = self.temp_dir.name
        self.ingest_api = ingest_api
        self.run_converter = SequencingRunConverter(self.ingest_api)
        self.logger = logging.getLogger(__name__)

    def submit_run_xml_files(self, manifests_ids: List[str], md5_file: str, ftp_parent_dir: str, action: str = 'ADD'):
        output = self.create_xml_files(manifests_ids, md5_file, ftp_parent_dir, action)
        run_xml_path = output['run_xml_path']
        submission_xml_path = output['submission_xml_path']

        files = [('SUBMISSION', open(submission_xml_path, 'r')), ('RUN', open(run_xml_path, 'r'))]
        receipt = self.post_files(files)

        all_run_data = output['all_run_data']
        self.save_receipt_to_file(receipt)

        report = self.process_receipt(receipt, all_run_data)
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        write_json(report, f'report_{timestamp}.json')

        return receipt

    def create_xml_files(self, manifests_ids: List[str], md5_file: str, ftp_parent_dir: str = '', action: str = 'ADD'):
        submission_xml_path = self.create_submission_xml(action)
        output = self.create_run_xml_from_manifests(manifests_ids, md5_file, ftp_parent_dir, action)
        output['submission_xml_path'] = submission_xml_path
        return output

    def create_run_xml_from_manifests(self, manifest_ids: List[str], md5_file: str, ftp_parent_dir: str = '',
                                      action: str = 'ADD'):
        all_run_data = []
        for manifest_id in manifest_ids:
            run_data = self.run_converter.prepare_sequencing_runs(manifest_id, md5_file, ftp_parent_dir, action)
            all_run_data.extend(run_data)

        run_xml_tree = self.run_converter.convert_sequencing_run_data_to_xml_tree(all_run_data)
        self.logger.debug(xml_to_string(run_xml_tree))
        run_xml_path = f'{self.xml_dir}/run.xml'
        try:
            write_xml(run_xml_tree, run_xml_path)
        except Exception as e:
            raise Error(f"An error occurred in writing the run xml : {str(e)}")
        return {
            'all_run_data': all_run_data,
            'run_xml_path': run_xml_path
        }

    def post_files(self, files: dict):
        self._require_env_vars()
        r = requests.post(self.url, files=files, auth=(self.user, self.password))
        r.raise_for_status()
        return r.text

    def _require_env_vars(self):
        if not self.url:
            raise Error('The ENA_WEBIN_API_URL be set in environment variables.')
        if not all([self.user, self.password]):
            raise Error('The ENA_USER, ENA_PASSWORD must be set in environment variables.')

    def process_receipt(self, result: str, runs: List[dict]):
        result_dict = load_xml_dict_from_string(result)
        accession_by_alias = self._get_accessions_from_receipt(result_dict)
        report = self._update_runs_with_accessions(accession_by_alias, runs)
        return report

    def _update_runs_with_accessions(self, accession_by_alias, runs):
        report = {
            'not_updated': [],
            'updated': []
        }
        for run in runs:
            alias = run.get('run_alias')
            accession = accession_by_alias.get(alias)
            files = run.get('files')
            self._update_files_with_accession(accession, alias, files, report)
        return report

    def _get_accessions_from_receipt(self, result_dict):
        accession_by_alias = {}
        run_xmls = result_dict['RECEIPT']['RUN']
        if not isinstance(run_xmls, list):
            run_xmls = [run_xmls]
        for run_xml in run_xmls:
            accession = run_xml.get('@accession')
            alias = run_xml.get('@alias')
            accession_by_alias[alias] = accession

            if not accession:
                self.logger.warning(f'Skipping the run with alias {alias} because it has no accession.')
                continue
        return accession_by_alias

    def _update_files_with_accession(self, accession, run_alias, files, report):
        for file in files:
            file_url = file.get('url')
            if not accession:
                report['not_updated'].append({
                    'file_url': file_url,
                    'alias': run_alias,
                    'error': 'no accession'
                })
                continue
            self._update_file_with_accession(accession, file_url)
            report['updated'].append({
                'file_url': file_url,
                'alias': run_alias,
                'accession': accession
            })

    def _update_file_with_accession(self, accession, file_url):
        file_json = self.ingest_api.get_entity(file_url)
        content = file_json.get('content', {})
        content['insdc_run_accessions'] = [accession]
        patch = {'content': content}
        self.ingest_api.patch(file_url, patch)

    def create_submission_xml(self, action: str = 'ADD'):
        if action.upper() not in SUBMIT_ACTIONS:
            raise Error(f'The submission action {action.upper()} is invalid, should be in {SUBMIT_ACTIONS}')

        submission_xml_as_string = f"""
        <SUBMISSION>
           <ACTIONS>
              <ACTION>
                 <{action.upper()}/>
              </ACTION>
           </ACTIONS>
        </SUBMISSION>
        """

        submission = ET.fromstring(submission_xml_as_string)
        submission_xml_tree = ET.ElementTree(submission)
        self.logger.debug(xml_to_string(submission_xml_tree))

        path = f'{self.xml_dir}/submission.xml'
        write_xml(submission_xml_tree, path)
        return path

    def save_receipt_to_file(self, receipt):
        result_tree = load_xml_tree_from_string(receipt)
        result_xml_tree = ET.ElementTree(result_tree)
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        write_xml(result_xml_tree, f'receipt_{timestamp}.xml')


class Error(Exception):
    """Base-class for all exceptions raised by this module."""
