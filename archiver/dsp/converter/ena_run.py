from conversion.post_process import default_to
from utils import protocols
from .abstracts import DspOntologyConverter


class EnaRunConverter(DspOntologyConverter):
    def convert(self, hca_data):
        process_spec = {
            '$on': 'process',
            'title': ['content.process_core.process_name', default_to, ''],
            'description': ['content.process_core.process_description', default_to, ''],
        }
        files_spec = {
            '$on': 'files',
            'name': ['content.file_core.file_name'],
            'format': ['content.file_core.format'],
            'uuid': ['uuid.uuid'],
            'lane_index': ['content.lane_index'],
            'read_index': ['content.read_index']
        }
        converted_data = self.map(hca_data, process_spec)
        converted_files = self.map(hca_data, files_spec)
        converted_data['attributes'] = self.map_file_attributes(converted_files)
        converted_data['files'] = self.map_files(converted_files, hca_data)
        return converted_data

    def map_file_attributes(self, converted_files):
        attributes = {}
        for index, file in enumerate(converted_files):
            file_attribute_spec = {
                f'Files - {index} - File Core - File Name': ['name', self.dsp_attribute],
                f'Files - {index} - File Core - Format': ['format', self.dsp_attribute],
                f'Files - {index} - HCA File UUID': ['uuid', self.dsp_attribute],
                f'Files - {index} - Read Index': ['read_index', self.dsp_attribute],
                f'Files - {index} - Lane Index': ['lane_index', self.dsp_attribute]
            }
            attributes.update(self.map(file, file_attribute_spec))
        return attributes

    def map_files(self, converted_files, hca_data):
        if protocols.is_10x(self.ontology_api, hca_data.get("library_preparation_protocol")):
            return self.bam_convert_files(hca_data)
        else:
            file_format_mapping = {
                'fastq.gz': 'fastq',
                'bam': 'bam',
                'cram': 'cram',
            }
            return [{
                'name': file.get('name'),
                'type': file_format_mapping.get(file.get('format'))
            } for file in converted_files]

    @staticmethod
    def bam_convert_files(hca_data):
        file_name = hca_data['manifest_id']
        if 'lane_index' in hca_data:
            file_name = f"{file_name}_{hca_data.get('lane_index')}"
        return [{
            'name': f'{file_name}.bam',
            'type': 'bam'
        }]
