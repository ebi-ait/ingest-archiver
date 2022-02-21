import logging
import functools
from api.ingest import IngestAPI
from converter.ena.ena_experiment import EnaExperiment
from converter.ena.ena_run import EnaRun
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig


class EnaArchive:
    def __init__(self, uuid):
        self.uuid = uuid
        self.data = HcaData(uuid).get()
        self.convert()

    def convert(self):
        config = SerializerConfig(pretty_print=True)
        serializer = XmlSerializer(config=config)

        experiment_set = EnaExperiment(self.data).create_set()
        print(serializer.render(experiment_set))

        run_set = EnaRun(self.data).create_set()
        print(serializer.render(run_set))


def handle_exception(f):
    @functools.wraps(f)
    def error(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except KeyError as e:
            logging.error(f'HcaData KeyError: source entity does not contain key: {str(e)}')
        except Exception as e:
            logging.error(f'HcaData Exception: {str(e)}')

    return error


class HcaData(IngestAPI):
    """
    Assay:
    [Biomaterial]  --> |   Process  |  -->  [File]
                       |     |      |
                       |     v      |
                       | [Protocol] |
    "submission": {
        ...
        "project": ...
        "assays": [
            {
                ... # process
                "sequencing_protocol": {...},
                "library_preparation_protocol": {...},
                "input_biomaterials": [...],
                "derived_files": [...]
            },
            ...
        ]
    }
    """
    def __init__(self, uuid):
        IngestAPI.__init__(self)
        self.logger = logging.getLogger(__name__)
        self.uuid = uuid

    @handle_exception
    def get(self):
        url = f'{self.url}/submissionEnvelopes/search/findByUuidUuid?uuid={self.uuid}'
        response = self.session.get(url, headers=self.headers)
        self.submission = None

        if response.ok:
            self.submission = response.json()

            # get project
            projects = self.get_submission_entities('projects')
            if projects:
                if len(projects) == 1:
                    self.submission["project"] = projects[0]
                    self.logger.info(f'Project UUID {self.submission["project"]["uuid"]["uuid"]}.')
                else:
                    self.logger.info(f'Multiple projects linked to submission {self.uuid}.')
            else:
                self.logger.info(
                    f'No project linked to submission {self.uuid}. Sequencing Experiment requires a study accession.')

        self.get_assays()

    def get_assays(self):
        assays = []
        # get processes
        processes = self.get_submission_entities('processes')
        num_processes = len(processes)
        self.logger.debug(f'{num_processes} processes in submission.')

        for index, process in enumerate(processes):

            self.logger.info(
                f"{index + 1}/{num_processes} Checking {process['content']['process_core']['process_id']}")
            # assay process protocol checks
            sequencing_protocol, library_preparation_protocol = self.get_sequencing_and_library_preparation_protocols(process)

            if not sequencing_protocol and not library_preparation_protocol:
                self.logger.info(f'No sequencing and library preparation protocols found.')
                continue

            process["sequencing_protocol"] = sequencing_protocol
            process["library_preparation_protocol"] = library_preparation_protocol

            # assay process input and output checks
            process["input_biomaterials"] = self.get_input_biomaterials(process)
            if not process["input_biomaterials"]:
                self.logger.info(f'No input biomaterials found.')
                continue

            process["derived_files"] = self.get_derived_files(process)
            if not process["derived_files"]:
                self.logger.info(f'No derived files found.')
                continue

            # rule out unexpected in/output
            if self.has_derived_biomaterials(process):
                self.logger.info('Not assay: has derived biomaterials.')
                continue

            if self.has_input_files(process):
                self.logger.info('Not assay: has input files.')
                continue

            if process["sequencing_protocol"] and process["library_preparation_protocol"] and process[
                "input_biomaterials"] and process["derived_files"]:
                assays.append(process)

        self.logger.info(f'{len(assays)} assay processes found.')
        self.submission["assays"] = assays

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

    def get_sequencing_and_library_preparation_protocols(self, process):
        protocols = self.get_all_entities(process["_links"]["protocols"]["href"], 'protocols', [])
        sequencing_protocol = None
        library_preparation_protocol = None
        for protocol in protocols:
            described_by = protocol["content"]["describedBy"]
            if described_by.endswith('sequencing_protocol'):
                sequencing_protocol = protocol
            elif described_by.endswith('library_preparation_protocol'):
                library_preparation_protocol = protocol
        return sequencing_protocol, library_preparation_protocol

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
        response = self.session.get(url, headers=self.headers)
        response.raise_for_status()
        if "_embedded" in response.json():
            entities += response.json()["_embedded"][entity_type]

            if "next" in response.json()["_links"]:
                url = response.json()["_links"]["next"]["href"]
                self.get_all_entities(url, entity_type, entities)
        return entities
