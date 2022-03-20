import unittest

from hca.assay import AssayData
from converter.ena.classes import TypeLibraryStrategy, TypeLibrarySource
from converter.ena.ena_experiment import EnaExperiment, HcaEnaMapping
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig


class TestEnaExperiment(unittest.TestCase):
    config = SerializerConfig(pretty_print=True)
    serializer = XmlSerializer(config=config)

    def test_valid_experiment(self):
        assay_data = EnaExperimentTestData.test_assay_data()

        experiment = EnaExperiment(EnaExperimentTestData.project_acc).create(assay_data.assays[0])
        generated_xml = self.serializer.render(experiment)

        self.assertEqual(generated_xml, EnaExperimentTestData.xml())


    def test_invalid_experiment_keyerror(self):
        assay_data = EnaExperimentTestData.test_assay_data()
        del assay_data.assays[0]["sequencing_protocol"]

        with self.assertRaises(KeyError):
            EnaExperiment(EnaExperimentTestData.project_acc).create(assay_data.assays[0])


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
    def test_assay_data():
        assay_data = AssayData(None, 'uuid')
        assay_data.project = {
            "content": {
                "insdc_project_accessions": [ EnaExperimentTestData.project_acc ]
            }}
        assay_data.assays = [
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
        return assay_data

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
      <LIBRARY_STRATEGY>{TypeLibraryStrategy.OTHER.value}</LIBRARY_STRATEGY>
      <LIBRARY_SOURCE>{TypeLibrarySource.TRANSCRIPTOMIC_SINGLE_CELL.value}</LIBRARY_SOURCE>
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
