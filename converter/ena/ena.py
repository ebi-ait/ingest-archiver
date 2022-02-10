import sys
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

        experiment_set = EnaExperiment(self.data).experiment_set()
        print(serializer.render(experiment_set))

        run_set = EnaRun(self.data).run_set()
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
        self.logger.info(f'{num_processes} processes in submission.')

        for index, process in enumerate(processes):

            self.logger.info(
                f"{index + 1}/{num_processes} Checking {process['content']['process_core']['process_id']}")

            protocols = self.get_all_entities(process["_links"]["protocols"]["href"], 'protocols', [])
            sequencing_protocol = None
            library_preparation_protocol = None

            for protocol in protocols:
                described_by = protocol["content"]["describedBy"]
                if described_by.endswith('sequencing_protocol'):
                    sequencing_protocol = protocol
                elif described_by.endswith('library_preparation_protocol'):
                    library_preparation_protocol = protocol

            if sequencing_protocol or library_preparation_protocol:
                self.logger.info(f'Process has sequencing and library preparation protocols.')
                process["sequencing_protocol"] = sequencing_protocol
                process["library_preparation_protocol"] = library_preparation_protocol
            else:
                self.logger.info(f'No sequencing and library preparation protocols found.')
                continue

            # get input biomaterials
            input_biomaterials = self.get_all_entities(process["_links"]["inputBiomaterials"]["href"],
                                                       'biomaterials', [])

            if input_biomaterials:
                self.logger.info(f'Process has input biomaterials.')
                process["input_biomaterials"] = input_biomaterials
            else:
                self.logger.info(f'No input biomaterials found.')
                continue

            # get derived files
            derived_files = self.get_all_entities(process["_links"]["derivedFiles"]["href"], 'files', [])

            if derived_files:
                self.logger.info(f'Process has derived files.')
                process["derived_files"] = derived_files
            else:
                self.logger.info(f'No derived files found.')
                continue

            # rule out unexpected in/output
            derived_biomaterials = self.get_all_entities(process["_links"]["derivedBiomaterials"]["href"],
                                                         'biomaterials', [])
            if derived_biomaterials:
                self.logger.info('Process has derived biomaterials.')
                continue

            input_files = self.get_all_entities(process["_links"]["inputFiles"]["href"], 'files', [])
            if input_files:
                self.logger.info('Process has input files')
                continue

            if process["sequencing_protocol"] and process["library_preparation_protocol"] and process[
                "input_biomaterials"] and process["derived_files"]:
                assays.append(process)

        self.logger.info(f'{len(assays)} assay processes found.')
        self.submission["assays"] = assays

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

format = ' %(asctime)s  - %(name)s - %(levelname)s in %(filename)s:' \
         '%(lineno)s %(funcName)s(): %(message)s'
logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                    format=format)

if __name__ == "__main__":
    ena = EnaArchive(uuid="76283647-9b00-4651-9224-18a4db2b7b29") # 8f44d9bb-527c-4d1d-b259-ee9ac62e11b6