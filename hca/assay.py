import logging
from api.ingest import IngestAPI
import sys

class AssayData:
    """
    Assay:
    [Biomaterial]  --> |   Process  |  -->  [File]
                       |     |      |
                       |     v      |
                       | [Protocol] |
    "submission": {...}
    "project": {...}
    "assays": [
        {
            ... # process
            "sequencing_protocol": {...},
            "library_preparation_protocols": [...],
            "input_biomaterials": [...],
            "derived_files": [...]
        },
        ...
    ]
    """
    def __init__(self, ingest_api: IngestAPI, uuid: str):
        self.logger = logging.getLogger(__name__)
        self.ingest_api = ingest_api
        self.uuid = uuid

    def load(self):
        self.submission = self.get_submission(self.uuid)
        self.project = self.get_submission_project()
        self.assays = self.get_submission_assays()

    def get_submission(self, uuid):
        try:
            submission = self.ingest_api.get_submission_by_uuid(uuid)
            return submission
        except Exception as e:
            raise Exception(f'Error retrieving submission {uuid}: {str(e)}')

    def get_submission_project(self):
        try:
            projects = self.get_all_entities(self.submission["_links"]["relatedProjects"]["href"], 'projects', [])
            if projects:
                if len(projects) == 1:
                    return projects[0]
                else:
                    raise Exception(f'Multiple projects linked to submission {self.uuid}.')
            else:
                raise Exception(f'No project linked to submission {self.uuid}.')
        except Exception as e:
            raise Exception(f'Error retrieving project for submission {self.uuid}: {str(e)}')

    def get_project_accession(self):
        try:
            accessions = self.project["content"]["insdc_project_accessions"]
            for accession in accessions:
                if accession.startswith("ERP"):
                    return accession
            raise Exception
        except:
            raise Exception('ENA sequencing experiment requires a project accession.')

    def get_submission_assays(self):
        try:
            return self.__get_submission_assays()
        except Exception as e:
            raise Exception(f'Error getting submission assays: {str(e)}')

    def __get_submission_assays(self):
        assays = []
        # get processes
        processes = self.get_submission_entities('processes')
        num_processes = len(processes)
        self.logger.debug(f'{num_processes} processes in submission.')

        for index, process in enumerate(processes):

            self.logger.info(
                f"{index + 1}/{num_processes} Checking {process['content']['process_core']['process_id']}")
            # assay process protocol checks
            sequencing_protocols, library_preparation_protocols = self.get_sequencing_and_library_preparation_protocols(process)
            num_sequencing_protocols = len(sequencing_protocols)
            num_library_preparation_protocols = len(library_preparation_protocols)
            if num_sequencing_protocols == 1 and num_library_preparation_protocols > 0:
                self.logger.info(f'Assay process sequencing and lib prep protocols found')
            else:
                self.logger.info(f'{num_sequencing_protocols} sequencing and {num_library_preparation_protocols} library preparation protocols found.')
                continue

            process["sequencing_protocol"] = sequencing_protocols[0]
            process["library_preparation_protocols"] = library_preparation_protocols

            # assay process input and output checks
            process["input_biomaterials"] = self.get_input_biomaterials(process)
            if not process["input_biomaterials"]:
                self.logger.info(f'No input biomaterials found.')
                continue

            process["derived_files"] = self.get_derived_files(process)
            if not process["derived_files"]:
                self.logger.info(f'No derived files found.')
                continue
            else:
                all_sequence_files = True
                for file in process["derived_files"]:
                    described_by = file["content"]["describedBy"]
                    all_sequence_files = all_sequence_files and described_by.endswith('sequence_file')
                if not all_sequence_files:
                    self.logger.info(f'Non sequence files found among derived files.')
                    continue

            # rule out unexpected in/output
            if self.has_derived_biomaterials(process):
                self.logger.info('Not assay: has derived biomaterials.')
                continue

            if self.has_input_files(process):
                self.logger.info('Not assay: has input files.')
                continue

            if process["sequencing_protocol"] and process["library_preparation_protocols"] and process[
                "input_biomaterials"] and process["derived_files"]:
                assays.append(process)

        self.logger.info(f'{len(assays)} assay processes found.')
        return assays

    def get_input_biomaterials(self, process):
        input_biomaterials = self.get_all_entities(process["_links"]["inputBiomaterials"]["href"],
                                                   'biomaterials', [])
        return input_biomaterials

    def get_derived_files(self, process):
        derived_files = self.get_all_entities(process["_links"]["derivedFiles"]["href"], 'files', [])
        return derived_files

    def has_derived_biomaterials(self, process):
        derived_biomaterials = self.get_all_entities(process["_links"]["derivedBiomaterials"]["href"],
                                                     'biomaterials', [])
        return True if derived_biomaterials else False

    def has_input_files(self, process):
        input_files = self.get_all_entities(process["_links"]["inputFiles"]["href"], 'files', [])
        return True if input_files else False

    # seq file can only be created by these 2 protocols
    def get_sequencing_and_library_preparation_protocols(self, process):
        protocols = self.get_all_entities(process["_links"]["protocols"]["href"], 'protocols', [])
        sequencing_protocols = []
        library_preparation_protocols = []
        for protocol in protocols:
            described_by = protocol["content"]["describedBy"]
            if described_by.endswith('sequencing_protocol'):
                sequencing_protocols.append(protocol)
            elif described_by.endswith('library_preparation_protocol'):
                library_preparation_protocols.append(protocol)
        return sequencing_protocols, library_preparation_protocols

    def get_submission_entities(self, entity_type):
        if self.submission:
            url = self.get_link(self.submission, entity_type)
            if url:
                return self.get_all_entities(url, entity_type, [])
        return []

    def get_link(self, json, entity):
        try:
            return json["_links"][entity]["href"]
        except KeyError:
            self.logger.error(f"No href link for entity {entity}")
            return None

    def get_all_entities(self, url, entity_type, entities=[]):
        response_json = self.ingest_api.get(url)
        if "_embedded" in response_json:
            entities += response_json["_embedded"][entity_type]

            if "next" in response_json["_links"]:
                url = response_json["_links"]["next"]["href"]
                self.get_all_entities(url, entity_type, entities)
        return entities

    def update_ingest_process_insdc_experiment_accession(self, process, experiment_accession):
        try:
            _links_self = process["_links"]["self"]["href"]
            entity_id = _links_self.split('/')[-1]
            logging.info(f"Patching ingest process {entity_id} with experiment accession {experiment_accession}")

            content = process["content"]
            insdc_experiment_accession = content.get("insdc_experiment", {}).get("insdc_experiment_accession")
            if not insdc_experiment_accession or (insdc_experiment_accession and insdc_experiment_accession != experiment_accession):
                content["insdc_experiment"] = {
                    "insdc_experiment_accession": experiment_accession
                }
                self.ingest_api.patch_entity_by_id('processes', entity_id, { 'content': content })
        except Exception as e:
            raise Exception(f"Error updating ingest process insdc_experiment_accession: {str(e)}")

    def update_ingest_file_insdc_run_accession(self, file, run_accession):
        try:
            _links_self = file["_links"]["self"]["href"]
            entity_id = _links_self.split('/')[-1]
            logging.info(f"Patching ingest file {entity_id} with run accession {run_accession}")

            content = file["content"]
            if "insdc_run_accessions" in content:
                if run_accession not in content["insdc_run_accessions"]:
                    content["insdc_run_accessions"].append(run_accession)
            else:
                content["insdc_run_accessions"] = [run_accession]

            self.ingest_api.patch_entity_by_id('files', entity_id, { 'content': content })

        except Exception as e:
            raise Exception(f"Error updating ingest file insdc_run_accessions: {str(e)}")



