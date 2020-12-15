from typing import List

from archiver.errors import ArchiverException


class Biomaterial:
    def __init__(self, data, derived_by_process=None, derived_with_protocols=None,
                 derived_from_biomaterials: List[dict] = None):
        self.data = data
        self.derived_by_process = derived_by_process
        self.derived_with_protocols = derived_with_protocols
        self.derived_from_biomaterials = derived_from_biomaterials if derived_from_biomaterials else None

    @classmethod
    def from_uuid(cls, ingest_api, biomaterial_uuid):
        data = ingest_api.get_biomaterial_by_uuid(biomaterial_uuid)

        derived_by_processes_count = ingest_api.get_related_entity_count(data, 'derivedByProcesses', 'processes')

        if derived_by_processes_count:
            derived_by_processes_iter = ingest_api.get_related_entity(data, 'derivedByProcesses', 'processes')
            derived_by_processes = list(derived_by_processes_iter)

            derived_with_protocols = {}
            derived_from_biomaterials = []
            for derived_by_process in derived_by_processes:
                derived_by_protocols = ingest_api.get_related_entity(derived_by_process, 'protocols', 'protocols')

                for protocol in derived_by_protocols:
                    protocol_type = ingest_api.get_concrete_entity_type(protocol)
                    if not derived_with_protocols.get(protocol_type):
                        derived_with_protocols[protocol_type] = []
                    derived_with_protocols[protocol_type].append(protocol)

                input_biomaterials_count = ingest_api.get_related_entity_count(
                    derived_by_process,
                    'inputBiomaterials',
                    'biomaterials'
                )
                if not input_biomaterials_count:
                    raise ArchiverException('A biomaterial has been derived by a process with no input biomaterial')

                input_biomaterials = ingest_api.get_related_entity(derived_by_process, 'inputBiomaterials', 'biomaterials')

                derived_from_biomaterials.extend(list(input_biomaterials))

            return cls(data, derived_by_process, derived_with_protocols, derived_from_biomaterials)
        else:
            return cls(data)
