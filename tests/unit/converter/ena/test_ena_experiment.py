import unittest

from converter.ena.ena import HcaData
from converter.ena.ena_experiment import EnaExperiment, HcaEnaMapping
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig


class TestEnaExperiment(unittest.TestCase):
    config = SerializerConfig(pretty_print=True)
    serializer = XmlSerializer(config=config)

    def test_valid_experiment(self):
        hca_data_valid = HcaData('uuid')
        hca_data_valid.submission = EnaExperimentTestData.submission()

        experiment = EnaExperiment(hca_data_valid).experiment(hca_data_valid.submission["assays"][0])
        generated_xml = self.serializer.render(experiment)

        self.assertEqual(generated_xml, EnaExperimentTestData.xml())


    def test_invalid_experiment_keyerror(self):
        hca_data_no_project_content = HcaData('uuid')
        hca_data_no_project_content.submission = EnaExperimentTestData.submission()
        del hca_data_no_project_content.submission["project"]["content"]

        with self.assertRaises(KeyError):
            EnaExperiment(hca_data_no_project_content).experiment(hca_data_no_project_content.submission["assays"][0])


class EnaExperimentTestData:

    project_acc = "PRJ009"
    protocol_id = "seq_protocol_1"
    protocol_name = "seq_protocol_1 name"
    protocol_desc = "seq_protocol_1 desc"
    instru_model = "Illumina NovaSeq 6000"
    lib_prep_primer = "poly-dT"
    biomat_id = "input_biomat_1"
    biomat_acc = "SAM007"

    @staticmethod
    def submission():
        return {"project": {
            "content": {
                "insdc_project_accessions": [ EnaExperimentTestData.project_acc ]
            }},
            "assays": [
            {
                "sequencing_protocol": {
                    "content":
                        {
                            "protocol_core": {
                                "protocol_id": EnaExperimentTestData.protocol_id,
                                "protocol_name": EnaExperimentTestData.protocol_name,
                                "protocol_description": EnaExperimentTestData.protocol_desc
                            },
                            "paired_end": True,
                            "instrument_manufacturer_model": {
                                "text": EnaExperimentTestData.instru_model
                            }
                        }
                },
                "library_preparation_protocol": {
                    "content":
                        {
                            "primer": EnaExperimentTestData.lib_prep_primer,
                        }
                },
                "input_biomaterials": [{
                    "content":
                        {
                            "biomaterial_core": {
                                "biomaterial_id": EnaExperimentTestData.biomat_id,
                                "biosamples_accession": EnaExperimentTestData.biomat_acc
                            }
                        }
                }]
            }
        ]
        }

    @staticmethod
    def xml():
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<EXPERIMENT alias="{EnaExperimentTestData.protocol_id}">
  <TITLE>{EnaExperimentTestData.protocol_name}</TITLE>
  <STUDY_REF accession="{EnaExperimentTestData.project_acc}"/>
  <DESIGN>
    <DESIGN_DESCRIPTION/>
    <SAMPLE_DESCRIPTOR accession="{EnaExperimentTestData.biomat_acc}"/>
    <LIBRARY_DESCRIPTOR>
      <LIBRARY_NAME>{EnaExperimentTestData.biomat_id}</LIBRARY_NAME>
      <LIBRARY_STRATEGY>OTHER</LIBRARY_STRATEGY>
      <LIBRARY_SOURCE>TRANSCRIPTOMIC SINGLE CELL</LIBRARY_SOURCE>
      <LIBRARY_SELECTION>{HcaEnaMapping.LIBRARY_SELECTION_MAPPING.get(EnaExperimentTestData.lib_prep_primer).value}</LIBRARY_SELECTION>
      <LIBRARY_LAYOUT>
        <PAIRED NOMINAL_LENGTH="0" NOMINAL_SDEV="0"/>
      </LIBRARY_LAYOUT>
    </LIBRARY_DESCRIPTOR>
  </DESIGN>
  <PLATFORM>
    <ILLUMINA>
      <INSTRUMENT_MODEL>{EnaExperimentTestData.instru_model}</INSTRUMENT_MODEL>
    </ILLUMINA>
  </PLATFORM>
  <EXPERIMENT_ATTRIBUTES>
    <EXPERIMENT_ATTRIBUTE>
      <TAG>Description</TAG>
      <VALUE>{EnaExperimentTestData.protocol_desc}</VALUE>
    </EXPERIMENT_ATTRIBUTE>
  </EXPERIMENT_ATTRIBUTES>
</EXPERIMENT>
"""
