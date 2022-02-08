from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

__NAMESPACE__ = "SRA.common"


@dataclass
class AttributeType:
    """
    Reusable attributes to encode tag-value pairs with optional units.

    :ivar tag: Name of the attribute.
    :ivar value: Value of the attribute.
    :ivar units: Optional scientific units.
    """
    tag: Optional[str] = field(
        default=None,
        metadata={
            "name": "TAG",
            "type": "Element",
            "namespace": "",
            "required": True,
        }
    )
    value: Optional[str] = field(
        default=None,
        metadata={
            "name": "VALUE",
            "type": "Element",
            "namespace": "",
        }
    )
    units: Optional[str] = field(
        default=None,
        metadata={
            "name": "UNITS",
            "type": "Element",
            "namespace": "",
        }
    )


class BasecallMatchEdge(Enum):
    """
    :cvar FULL: Only @max_mismatch influences matching process
    :cvar START: Both matches and mismatches are counted. When
        @max_mismatch is exceeded - it is not a match. When @min_match
        is reached - match is declared.
    :cvar END: Both matches and mismatches are counted. When
        @max_mismatch is exceeded - it is not a match. When @min_match
        is reached - match is declared.
    """
    FULL = "full"
    START = "start"
    END = "end"


@dataclass
class NameType:
    """
    :ivar value:
    :ivar label: Alternative/explanatory description of the same
        object/identifier.
    """
    value: str = field(
        default="",
        metadata={
            "required": True,
        }
    )
    label: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )


@dataclass
class PipelineType:
    """
    The PipelineType identifies the sequence or tree of actions to process the
    sequencing data.
    """
    pipe_section: List["PipelineType.PipeSection"] = field(
        default_factory=list,
        metadata={
            "name": "PIPE_SECTION",
            "type": "Element",
            "namespace": "",
            "min_occurs": 1,
        }
    )

    @dataclass
    class PipeSection:
        """
        :ivar step_index: Lexically ordered  value that allows for the
            pipe section to be hierarchically ordered.  The float
            primitive data type is used to allow for pipe sections to be
            inserted later on.
        :ivar prev_step_index: STEP_INDEX of the previous step in the
            workflow.  Set toNIL if the first pipe section.
        :ivar program: Name of the program or process for primary
            analysis.   This may include a test or condition that leads
            to branching in the workflow.
        :ivar version: Version of the program or process for primary
            analysis.
        :ivar notes: Notes about the program or process for primary
            analysis.
        :ivar section_name: Name of the processing pipeline section.
        """
        step_index: Optional[str] = field(
            default=None,
            metadata={
                "name": "STEP_INDEX",
                "type": "Element",
                "namespace": "",
                "required": True,
            }
        )
        prev_step_index: List[str] = field(
            default_factory=list,
            metadata={
                "name": "PREV_STEP_INDEX",
                "type": "Element",
                "namespace": "",
                "min_occurs": 1,
                "nillable": True,
            }
        )
        program: Optional[str] = field(
            default=None,
            metadata={
                "name": "PROGRAM",
                "type": "Element",
                "namespace": "",
                "required": True,
            }
        )
        version: Optional[str] = field(
            default=None,
            metadata={
                "name": "VERSION",
                "type": "Element",
                "namespace": "",
                "required": True,
            }
        )
        notes: Optional[str] = field(
            default=None,
            metadata={
                "name": "NOTES",
                "type": "Element",
                "namespace": "",
            }
        )
        section_name: Optional[str] = field(
            default=None,
            metadata={
                "type": "Attribute",
            }
        )


class ReadSpecReadClass(Enum):
    APPLICATION_READ = "Application Read"
    TECHNICAL_READ = "Technical Read"


class ReadSpecReadType(Enum):
    FORWARD = "Forward"
    REVERSE = "Reverse"
    ADAPTER = "Adapter"
    PRIMER = "Primer"
    LINKER = "Linker"
    BAR_CODE = "BarCode"
    OTHER = "Other"


@dataclass
class ReferenceAssemblyType:
    """
    Reference assembly details.

    :ivar standard: A standard genome assembly.
    :ivar custom: Other genome assembly.
    """
    standard: Optional["ReferenceAssemblyType.Standard"] = field(
        default=None,
        metadata={
            "name": "STANDARD",
            "type": "Element",
            "namespace": "",
        }
    )
    custom: Optional["ReferenceAssemblyType.Custom"] = field(
        default=None,
        metadata={
            "name": "CUSTOM",
            "type": "Element",
            "namespace": "",
        }
    )

    @dataclass
    class Standard:
        """
        :ivar refname: A recognized name for the genome assembly.
        :ivar accession: Identifies the genome assembly using an
            accession number and a sequence version.
        """
        refname: Optional[str] = field(
            default=None,
            metadata={
                "type": "Attribute",
            }
        )
        accession: Optional[str] = field(
            default=None,
            metadata={
                "type": "Attribute",
            }
        )

    @dataclass
    class Custom:
        """
        :ivar description: Description of the genome assembly.
        :ivar url_link: A link to the genome assembly.
        """
        description: Optional[str] = field(
            default=None,
            metadata={
                "name": "DESCRIPTION",
                "type": "Element",
                "namespace": "",
            }
        )
        url_link: List["ReferenceAssemblyType.Custom.UrlLink"] = field(
            default_factory=list,
            metadata={
                "name": "URL_LINK",
                "type": "Element",
                "namespace": "",
                "min_occurs": 1,
            }
        )

        @dataclass
        class UrlLink:
            """
            :ivar label: Text label to display for the link.
            :ivar url: The internet service link (file:, http:, ftp:,
                etc).
            """
            label: Optional[str] = field(
                default=None,
                metadata={
                    "name": "LABEL",
                    "type": "Element",
                    "namespace": "",
                }
            )
            url: Optional[str] = field(
                default=None,
                metadata={
                    "name": "URL",
                    "type": "Element",
                    "namespace": "",
                    "required": True,
                }
            )


class SequencingDirectivesTypeSampleDemuxDirective(Enum):
    """
    :cvar LEAVE_AS_POOL: There shall be no sample de-multiplexing at the
        level of assiging individual reads to sample pool members.
    :cvar SUBMITTER_DEMULTIPLEXED: The submitter has assigned individual
        reads to sample pool members by providing individual files
        containing reads with the same member assignment.
    """
    LEAVE_AS_POOL = "leave_as_pool"
    SUBMITTER_DEMULTIPLEXED = "submitter_demultiplexed"


@dataclass
class Urltype:
    """
    :ivar label: Text label to display for the link.
    :ivar url: The internet service link (file:, http:, ftp:, etc).
    """
    class Meta:
        name = "URLType"

    label: Optional[str] = field(
        default=None,
        metadata={
            "name": "LABEL",
            "type": "Element",
            "namespace": "",
            "required": True,
        }
    )
    url: Optional[str] = field(
        default=None,
        metadata={
            "name": "URL",
            "type": "Element",
            "namespace": "",
            "required": True,
        }
    )


@dataclass
class XrefType:
    """
    :ivar db: INSDC controlled vocabulary of permitted cross references.
        Please see http://www.insdc.org/db_xref.html . For example,
        FLYBASE.
    :ivar id: Accession in the referenced database.    For example,
        FBtr0080008 (in FLYBASE).
    :ivar label: Text label to display for the link.
    """
    class Meta:
        name = "XRefType"

    db: Optional[str] = field(
        default=None,
        metadata={
            "name": "DB",
            "type": "Element",
            "namespace": "",
            "required": True,
        }
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "ID",
            "type": "Element",
            "namespace": "",
            "required": True,
        }
    )
    label: Optional[str] = field(
        default=None,
        metadata={
            "name": "LABEL",
            "type": "Element",
            "namespace": "",
        }
    )


class Type454Model(Enum):
    VALUE_454_GS = "454 GS"
    VALUE_454_GS_20 = "454 GS 20"
    VALUE_454_GS_FLX = "454 GS FLX"
    VALUE_454_GS_FLX_1 = "454 GS FLX+"
    VALUE_454_GS_FLX_TITANIUM = "454 GS FLX Titanium"
    VALUE_454_GS_JUNIOR = "454 GS Junior"
    UNSPECIFIED = "unspecified"


class TypeAbiSolidModel(Enum):
    """
    :cvar AB_SOLI_D_SYSTEM: Undifferentiated early AB SOLiD system
    :cvar AB_SOLI_D_SYSTEM_2_0:
    :cvar AB_SOLI_D_SYSTEM_3_0:
    :cvar AB_SOLI_D_3_PLUS_SYSTEM:
    :cvar AB_SOLI_D_4_SYSTEM:
    :cvar AB_SOLI_D_4HQ_SYSTEM:
    :cvar AB_SOLI_D_PI_SYSTEM:
    :cvar AB_5500_GENETIC_ANALYZER:
    :cvar AB_5500XL_GENETIC_ANALYZER:
    :cvar AB_5500XL_W_GENETIC_ANALYSIS_SYSTEM:
    :cvar UNSPECIFIED:
    """
    AB_SOLI_D_SYSTEM = "AB SOLiD System"
    AB_SOLI_D_SYSTEM_2_0 = "AB SOLiD System 2.0"
    AB_SOLI_D_SYSTEM_3_0 = "AB SOLiD System 3.0"
    AB_SOLI_D_3_PLUS_SYSTEM = "AB SOLiD 3 Plus System"
    AB_SOLI_D_4_SYSTEM = "AB SOLiD 4 System"
    AB_SOLI_D_4HQ_SYSTEM = "AB SOLiD 4hq System"
    AB_SOLI_D_PI_SYSTEM = "AB SOLiD PI System"
    AB_5500_GENETIC_ANALYZER = "AB 5500 Genetic Analyzer"
    AB_5500XL_GENETIC_ANALYZER = "AB 5500xl Genetic Analyzer"
    AB_5500XL_W_GENETIC_ANALYSIS_SYSTEM = "AB 5500xl-W Genetic Analysis System"
    UNSPECIFIED = "unspecified"


class TypeBgiseqmodel(Enum):
    BGISEQ_50 = "BGISEQ-50"
    BGISEQ_500 = "BGISEQ-500"
    MGISEQ_2000_RS = "MGISEQ-2000RS"


class TypeCgmodel(Enum):
    COMPLETE_GENOMICS = "Complete Genomics"
    UNSPECIFIED = "unspecified"


class TypeCapillaryModel(Enum):
    AB_3730X_L_GENETIC_ANALYZER = "AB 3730xL Genetic Analyzer"
    AB_3730_GENETIC_ANALYZER = "AB 3730 Genetic Analyzer"
    AB_3500X_L_GENETIC_ANALYZER = "AB 3500xL Genetic Analyzer"
    AB_3500_GENETIC_ANALYZER = "AB 3500 Genetic Analyzer"
    AB_3130X_L_GENETIC_ANALYZER = "AB 3130xL Genetic Analyzer"
    AB_3130_GENETIC_ANALYZER = "AB 3130 Genetic Analyzer"
    AB_310_GENETIC_ANALYZER = "AB 310 Genetic Analyzer"
    UNSPECIFIED = "unspecified"


class TypeDnbSeqModel(Enum):
    DNBSEQ_T7 = "DNBSEQ-T7"
    DNBSEQ_G400 = "DNBSEQ-G400"
    DNBSEQ_G50 = "DNBSEQ-G50"
    DNBSEQ_G400_FAST = "DNBSEQ-G400 FAST"
    UNSPECIFIED = "unspecified"


class TypeHelicosModel(Enum):
    HELICOS_HELI_SCOPE = "Helicos HeliScope"
    UNSPECIFIED = "unspecified"


class TypeIlluminaModel(Enum):
    HI_SEQ_X_FIVE = "HiSeq X Five"
    HI_SEQ_X_TEN = "HiSeq X Ten"
    ILLUMINA_GENOME_ANALYZER = "Illumina Genome Analyzer"
    ILLUMINA_GENOME_ANALYZER_II = "Illumina Genome Analyzer II"
    ILLUMINA_GENOME_ANALYZER_IIX = "Illumina Genome Analyzer IIx"
    ILLUMINA_HI_SCAN_SQ = "Illumina HiScanSQ"
    ILLUMINA_HI_SEQ_1000 = "Illumina HiSeq 1000"
    ILLUMINA_HI_SEQ_1500 = "Illumina HiSeq 1500"
    ILLUMINA_HI_SEQ_2000 = "Illumina HiSeq 2000"
    ILLUMINA_HI_SEQ_2500 = "Illumina HiSeq 2500"
    ILLUMINA_HI_SEQ_3000 = "Illumina HiSeq 3000"
    ILLUMINA_HI_SEQ_4000 = "Illumina HiSeq 4000"
    ILLUMINA_HI_SEQ_X = "Illumina HiSeq X"
    ILLUMINA_I_SEQ_100 = "Illumina iSeq 100"
    ILLUMINA_MI_SEQ = "Illumina MiSeq"
    ILLUMINA_MINI_SEQ = "Illumina MiniSeq"
    ILLUMINA_NOVA_SEQ_6000 = "Illumina NovaSeq 6000"
    NEXT_SEQ_500 = "NextSeq 500"
    NEXT_SEQ_550 = "NextSeq 550"
    NEXT_SEQ_1000 = "NextSeq 1000"
    NEXT_SEQ_2000 = "NextSeq 2000"
    UNSPECIFIED = "unspecified"


class TypeIontorrentModel(Enum):
    ION_TORRENT_PGM = "Ion Torrent PGM"
    ION_TORRENT_PROTON = "Ion Torrent Proton"
    ION_TORRENT_S5 = "Ion Torrent S5"
    ION_TORRENT_S5_XL = "Ion Torrent S5 XL"
    ION_TORRENT_GENEXUS = "Ion Torrent Genexus"
    ION_GENE_STUDIO_S5 = "Ion GeneStudio S5"
    ION_GENE_STUDIO_S5_PRIME = "Ion GeneStudio S5 Prime"
    ION_GENE_STUDIO_S5_PLUS = "Ion GeneStudio S5 Plus"
    UNSPECIFIED = "unspecified"


class TypeOxfordNanoporeModel(Enum):
    MIN_ION = "MinION"
    GRID_ION = "GridION"
    PROMETH_ION = "PromethION"
    UNSPECIFIED = "unspecified"


class TypePacBioModel(Enum):
    PAC_BIO_RS = "PacBio RS"
    PAC_BIO_RS_II = "PacBio RS II"
    SEQUEL = "Sequel"
    SEQUEL_II = "Sequel II"
    UNSPECIFIED = "unspecified"


@dataclass
class LinkType:
    """
    Reusable external links type to encode URL links, Entrez links, and db_xref
    links.
    """
    url_link: Optional["LinkType.UrlLink"] = field(
        default=None,
        metadata={
            "name": "URL_LINK",
            "type": "Element",
            "namespace": "",
        }
    )
    xref_link: Optional[XrefType] = field(
        default=None,
        metadata={
            "name": "XREF_LINK",
            "type": "Element",
            "namespace": "",
        }
    )
    entrez_link: Optional["LinkType.EntrezLink"] = field(
        default=None,
        metadata={
            "name": "ENTREZ_LINK",
            "type": "Element",
            "namespace": "",
        }
    )

    @dataclass
    class UrlLink:
        """
        :ivar label: Text label to display for the link.
        :ivar url: The internet service link (file:, http:, ftp: etc).
        """
        label: Optional[str] = field(
            default=None,
            metadata={
                "name": "LABEL",
                "type": "Element",
                "namespace": "",
                "required": True,
            }
        )
        url: Optional[str] = field(
            default=None,
            metadata={
                "name": "URL",
                "type": "Element",
                "namespace": "",
                "required": True,
            }
        )

    @dataclass
    class EntrezLink:
        """
        :ivar db: NCBI controlled vocabulary of permitted cross
            references.  Please see
            http://www.ncbi.nlm.nih.gov/entrez/eutils/einfo.fcgi? .
        :ivar id: Numeric record id meaningful to the NCBI Entrez
            system.
        :ivar query: Accession string meaningful to the NCBI Entrez
            system.
        :ivar label: How to label the link.
        """
        db: Optional[str] = field(
            default=None,
            metadata={
                "name": "DB",
                "type": "Element",
                "namespace": "",
                "required": True,
            }
        )
        id: Optional[int] = field(
            default=None,
            metadata={
                "name": "ID",
                "type": "Element",
                "namespace": "",
            }
        )
        query: Optional[str] = field(
            default=None,
            metadata={
                "name": "QUERY",
                "type": "Element",
                "namespace": "",
            }
        )
        label: Optional[str] = field(
            default=None,
            metadata={
                "name": "LABEL",
                "type": "Element",
                "namespace": "",
            }
        )


@dataclass
class PlatformType:
    """The PLATFORM record selects which sequencing platform and platform-
    specific runtime parameters.

    This will be determined by the Center.

    :ivar ls454: 454 technology use 1-color sequential flows
    :ivar illumina: Illumina is 4-channel flowgram with 1-to-1 mapping
        between basecalls and flows
    :ivar helicos: Helicos is similar to 454 technology - uses 1-color
        sequential flows
    :ivar abi_solid: ABI is 4-channel flowgram with 1-to-1 mapping
        between basecalls and flows
    :ivar complete_genomics: CompleteGenomics platform type. At present
        there is no instrument model.
    :ivar bgiseq:
    :ivar oxford_nanopore: Oxford Nanopore platform type. nanopore-based
        electronic single molecule analysis
    :ivar pacbio_smrt: PacificBiosciences platform type for the single
        molecule real time (SMRT) technology.
    :ivar ion_torrent: Ion Torrent Personal Genome Machine (PGM) from
        Life Technologies.
    :ivar capillary: Sequencers based on capillary electrophoresis
        technology manufactured by LifeTech (formerly Applied
        BioSciences).
    :ivar dnbseq: Sequencers based on DNBSEQ by MGI Tech.
    """
    ls454: Optional["PlatformType.Ls454"] = field(
        default=None,
        metadata={
            "name": "LS454",
            "type": "Element",
            "namespace": "",
        }
    )
    illumina: Optional["PlatformType.Illumina"] = field(
        default=None,
        metadata={
            "name": "ILLUMINA",
            "type": "Element",
            "namespace": "",
        }
    )
    helicos: Optional["PlatformType.Helicos"] = field(
        default=None,
        metadata={
            "name": "HELICOS",
            "type": "Element",
            "namespace": "",
        }
    )
    abi_solid: Optional["PlatformType.AbiSolid"] = field(
        default=None,
        metadata={
            "name": "ABI_SOLID",
            "type": "Element",
            "namespace": "",
        }
    )
    complete_genomics: Optional["PlatformType.CompleteGenomics"] = field(
        default=None,
        metadata={
            "name": "COMPLETE_GENOMICS",
            "type": "Element",
            "namespace": "",
        }
    )
    bgiseq: Optional["PlatformType.Bgiseq"] = field(
        default=None,
        metadata={
            "name": "BGISEQ",
            "type": "Element",
            "namespace": "",
        }
    )
    oxford_nanopore: Optional["PlatformType.OxfordNanopore"] = field(
        default=None,
        metadata={
            "name": "OXFORD_NANOPORE",
            "type": "Element",
            "namespace": "",
        }
    )
    pacbio_smrt: Optional["PlatformType.PacbioSmrt"] = field(
        default=None,
        metadata={
            "name": "PACBIO_SMRT",
            "type": "Element",
            "namespace": "",
        }
    )
    ion_torrent: Optional["PlatformType.IonTorrent"] = field(
        default=None,
        metadata={
            "name": "ION_TORRENT",
            "type": "Element",
            "namespace": "",
        }
    )
    capillary: Optional["PlatformType.Capillary"] = field(
        default=None,
        metadata={
            "name": "CAPILLARY",
            "type": "Element",
            "namespace": "",
        }
    )
    dnbseq: Optional["PlatformType.Dnbseq"] = field(
        default=None,
        metadata={
            "name": "DNBSEQ",
            "type": "Element",
            "namespace": "",
        }
    )

    @dataclass
    class Ls454:
        instrument_model: Optional[Type454Model] = field(
            default=None,
            metadata={
                "name": "INSTRUMENT_MODEL",
                "type": "Element",
                "namespace": "",
                "required": True,
            }
        )

    @dataclass
    class Illumina:
        instrument_model: Optional[TypeIlluminaModel] = field(
            default=None,
            metadata={
                "name": "INSTRUMENT_MODEL",
                "type": "Element",
                "namespace": "",
                "required": True,
            }
        )

    @dataclass
    class Helicos:
        instrument_model: Optional[TypeHelicosModel] = field(
            default=None,
            metadata={
                "name": "INSTRUMENT_MODEL",
                "type": "Element",
                "namespace": "",
                "required": True,
            }
        )

    @dataclass
    class AbiSolid:
        instrument_model: Optional[TypeAbiSolidModel] = field(
            default=None,
            metadata={
                "name": "INSTRUMENT_MODEL",
                "type": "Element",
                "namespace": "",
                "required": True,
            }
        )

    @dataclass
    class CompleteGenomics:
        instrument_model: Optional[TypeCgmodel] = field(
            default=None,
            metadata={
                "name": "INSTRUMENT_MODEL",
                "type": "Element",
                "namespace": "",
                "required": True,
            }
        )

    @dataclass
    class Bgiseq:
        instrument_model: Optional[TypeBgiseqmodel] = field(
            default=None,
            metadata={
                "name": "INSTRUMENT_MODEL",
                "type": "Element",
                "namespace": "",
                "required": True,
            }
        )

    @dataclass
    class OxfordNanopore:
        instrument_model: Optional[TypeOxfordNanoporeModel] = field(
            default=None,
            metadata={
                "name": "INSTRUMENT_MODEL",
                "type": "Element",
                "namespace": "",
                "required": True,
            }
        )

    @dataclass
    class PacbioSmrt:
        instrument_model: Optional[TypePacBioModel] = field(
            default=None,
            metadata={
                "name": "INSTRUMENT_MODEL",
                "type": "Element",
                "namespace": "",
                "required": True,
            }
        )

    @dataclass
    class IonTorrent:
        instrument_model: Optional[TypeIontorrentModel] = field(
            default=None,
            metadata={
                "name": "INSTRUMENT_MODEL",
                "type": "Element",
                "namespace": "",
                "required": True,
            }
        )

    @dataclass
    class Capillary:
        instrument_model: Optional[TypeCapillaryModel] = field(
            default=None,
            metadata={
                "name": "INSTRUMENT_MODEL",
                "type": "Element",
                "namespace": "",
                "required": True,
            }
        )

    @dataclass
    class Dnbseq:
        instrument_model: Optional[TypeDnbSeqModel] = field(
            default=None,
            metadata={
                "name": "INSTRUMENT_MODEL",
                "type": "Element",
                "namespace": "",
                "required": True,
            }
        )


@dataclass
class QualifiedNameType(NameType):
    """
    :ivar namespace: A string value that constrains the domain of named
        identifiers (namespace).
    """
    namespace: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        }
    )


@dataclass
class ReferenceSequenceType:
    """
    Reference assembly and sequence details.

    :ivar assembly: Reference assembly details.
    :ivar sequence: Reference sequence details.
    """
    assembly: Optional[ReferenceAssemblyType] = field(
        default=None,
        metadata={
            "name": "ASSEMBLY",
            "type": "Element",
            "namespace": "",
        }
    )
    sequence: List["ReferenceSequenceType.Sequence"] = field(
        default_factory=list,
        metadata={
            "name": "SEQUENCE",
            "type": "Element",
            "namespace": "",
        }
    )

    @dataclass
    class Sequence:
        """
        :ivar refname: A recognized name for the reference sequence.
        :ivar accession: Accession.version with version being mandatory
        :ivar label: This is how Reference Sequence is labeled in
            submission file(s). It is equivalent to  SQ label in BAM.
            Optional when submitted file uses INSDC accession.version
        """
        refname: Optional[str] = field(
            default=None,
            metadata={
                "type": "Attribute",
            }
        )
        accession: Optional[str] = field(
            default=None,
            metadata={
                "type": "Attribute",
            }
        )
        label: Optional[str] = field(
            default=None,
            metadata={
                "type": "Attribute",
            }
        )


@dataclass
class SequencingDirectivesType:
    """
    :ivar sample_demux_directive: Tells the Archive who will execute the
        sample demultiplexing operation..
    """
    sample_demux_directive: Optional[SequencingDirectivesTypeSampleDemuxDirective] = field(
        default=None,
        metadata={
            "name": "SAMPLE_DEMUX_DIRECTIVE",
            "type": "Element",
            "namespace": "",
        }
    )


@dataclass
class SpotDescriptorType:
    """The SPOT_DESCRIPTOR specifies how to decode the individual reads of
    interest from the monolithic spot sequence.

    The spot descriptor contains aspects of the experimental design,
    platform, and processing information.  There will be two methods of
    specification: one will be an index into a table of typical
    decodings, the other being an exact specification.
    """
    spot_decode_spec: Optional["SpotDescriptorType.SpotDecodeSpec"] = field(
        default=None,
        metadata={
            "name": "SPOT_DECODE_SPEC",
            "type": "Element",
            "namespace": "",
        }
    )

    @dataclass
    class SpotDecodeSpec:
        """
        :ivar spot_length: Number of base/color calls, cycles, or flows
            per spot (raw sequence length or flow length including all
            application and technical tags and mate pairs, but not
            including gap lengths). This value will be platform
            dependent, library dependent, and possibly run dependent.
            Variable length platforms will still have a constant
            flow/cycle length.
        :ivar read_spec:
        """
        spot_length: Optional[int] = field(
            default=None,
            metadata={
                "name": "SPOT_LENGTH",
                "type": "Element",
                "namespace": "",
            }
        )
        read_spec: List["SpotDescriptorType.SpotDecodeSpec.ReadSpec"] = field(
            default_factory=list,
            metadata={
                "name": "READ_SPEC",
                "type": "Element",
                "namespace": "",
                "min_occurs": 1,
            }
        )

        @dataclass
        class ReadSpec:
            """
            :ivar read_index: READ_INDEX starts at 0 and is
                incrementally increased for each sequential READ_SPEC
                within a SPOT_DECODE_SPEC
            :ivar read_label: READ_LABEL is a name for this tag, and can
                be used to on output to determine read name, for example
                F or R.
            :ivar read_class:
            :ivar read_type:
            :ivar relative_order: The read is located beginning at the
                offset or cycle relative to another read. This choice is
                appropriate for example when specifying a read that
                follows a variable length expected sequence(s).
            :ivar base_coord: The location of the read start in terms of
                base count (1 is beginning of spot).
            :ivar expected_basecall_table: A set of choices of expected
                basecalls for a current read. Read will be zero-length
                if none is found.
            """
            read_index: Optional[int] = field(
                default=None,
                metadata={
                    "name": "READ_INDEX",
                    "type": "Element",
                    "namespace": "",
                    "required": True,
                }
            )
            read_label: Optional[str] = field(
                default=None,
                metadata={
                    "name": "READ_LABEL",
                    "type": "Element",
                    "namespace": "",
                }
            )
            read_class: Optional[ReadSpecReadClass] = field(
                default=None,
                metadata={
                    "name": "READ_CLASS",
                    "type": "Element",
                    "namespace": "",
                    "required": True,
                }
            )
            read_type: ReadSpecReadType = field(
                default=ReadSpecReadType.FORWARD,
                metadata={
                    "name": "READ_TYPE",
                    "type": "Element",
                    "namespace": "",
                    "required": True,
                }
            )
            relative_order: Optional["SpotDescriptorType.SpotDecodeSpec.ReadSpec.RelativeOrder"] = field(
                default=None,
                metadata={
                    "name": "RELATIVE_ORDER",
                    "type": "Element",
                    "namespace": "",
                }
            )
            base_coord: Optional[int] = field(
                default=None,
                metadata={
                    "name": "BASE_COORD",
                    "type": "Element",
                    "namespace": "",
                }
            )
            expected_basecall_table: Optional["SpotDescriptorType.SpotDecodeSpec.ReadSpec.ExpectedBasecallTable"] = field(
                default=None,
                metadata={
                    "name": "EXPECTED_BASECALL_TABLE",
                    "type": "Element",
                    "namespace": "",
                }
            )

            @dataclass
            class RelativeOrder:
                """
                :ivar follows_read_index: Specify the read index that
                    precedes this read.
                :ivar precedes_read_index: Specify the read index that
                    follows this read.
                """
                follows_read_index: Optional[int] = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                    }
                )
                precedes_read_index: Optional[int] = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                    }
                )

            @dataclass
            class ExpectedBasecallTable:
                """
                :ivar basecall: Element's body contains a basecall,
                    attribute provide description of this read meaning
                    as well as matching rules.
                :ivar default_length: Specify whether the spot should
                    have a default length for this tag if the expected
                    base cannot be matched.
                :ivar base_coord: Specify an optional starting point for
                    tag (base offset from 1).
                """
                basecall: List["SpotDescriptorType.SpotDecodeSpec.ReadSpec.ExpectedBasecallTable.Basecall"] = field(
                    default_factory=list,
                    metadata={
                        "name": "BASECALL",
                        "type": "Element",
                        "namespace": "",
                        "min_occurs": 1,
                    }
                )
                default_length: Optional[int] = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                    }
                )
                base_coord: Optional[int] = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                    }
                )

                @dataclass
                class Basecall:
                    """
                    :ivar value:
                    :ivar read_group_tag: When match occurs, the read
                        will be tagged with this group membership
                    :ivar min_match: Minimum number of matches to
                        trigger identification.
                    :ivar max_mismatch: Maximum number of mismatches
                    :ivar match_edge: Where the match should occur.
                        Changes the rules on how min_match and
                        max_mismatch are counted.
                    """
                    value: str = field(
                        default="",
                        metadata={
                            "required": True,
                        }
                    )
                    read_group_tag: Optional[str] = field(
                        default=None,
                        metadata={
                            "type": "Attribute",
                        }
                    )
                    min_match: Optional[int] = field(
                        default=None,
                        metadata={
                            "type": "Attribute",
                        }
                    )
                    max_mismatch: Optional[int] = field(
                        default=None,
                        metadata={
                            "type": "Attribute",
                        }
                    )
                    match_edge: Optional[BasecallMatchEdge] = field(
                        default=None,
                        metadata={
                            "type": "Attribute",
                        }
                    )


@dataclass
class IdentifierType:
    """
    Set of record identifiers.

    :ivar primary_id: A primary identifier in the INSDC namespace.
    :ivar secondary_id: A secondary identifier in the INSDC namespace.
    :ivar external_id: An identifer rom a public non-INSDC resource.
    :ivar submitter_id: A submitter provided identifier.
    :ivar uuid: A universally unique identifier that requires no
        namespace.
    """
    primary_id: Optional[NameType] = field(
        default=None,
        metadata={
            "name": "PRIMARY_ID",
            "type": "Element",
            "namespace": "",
        }
    )
    secondary_id: List[NameType] = field(
        default_factory=list,
        metadata={
            "name": "SECONDARY_ID",
            "type": "Element",
            "namespace": "",
        }
    )
    external_id: List[QualifiedNameType] = field(
        default_factory=list,
        metadata={
            "name": "EXTERNAL_ID",
            "type": "Element",
            "namespace": "",
        }
    )
    submitter_id: Optional[QualifiedNameType] = field(
        default=None,
        metadata={
            "name": "SUBMITTER_ID",
            "type": "Element",
            "namespace": "",
        }
    )
    uuid: List[NameType] = field(
        default_factory=list,
        metadata={
            "name": "UUID",
            "type": "Element",
            "namespace": "",
        }
    )


@dataclass
class ProcessingType:
    """
    :ivar pipeline: Generic processing pipeline specification.
    :ivar directives: Processing directives tell the Sequence Read
        Archive how to treat the input data, if any treatment is
        requested.
    """
    pipeline: Optional[PipelineType] = field(
        default=None,
        metadata={
            "name": "PIPELINE",
            "type": "Element",
            "namespace": "",
        }
    )
    directives: Optional[SequencingDirectivesType] = field(
        default=None,
        metadata={
            "name": "DIRECTIVES",
            "type": "Element",
            "namespace": "",
        }
    )


@dataclass
class ObjectType:
    """
    :ivar identifiers:
    :ivar alias: Submitter designated name for the object. The name must
        be unique within the submission account.
    :ivar center_name: The center name of the submitter.
    :ivar broker_name: The center name of the broker.
    :ivar accession: The object accession assigned by the archive.
    """
    identifiers: Optional[IdentifierType] = field(
        default=None,
        metadata={
            "name": "IDENTIFIERS",
            "type": "Element",
            "namespace": "",
        }
    )
    alias: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )
    center_name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )
    broker_name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )
    accession: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )


@dataclass
class RefObjectType:
    """
    :ivar identifiers:
    :ivar refname: Identifies an object by name within the namespace
        defined by attribute "refcenter".
    :ivar refcenter: The namespace of the attribute "refname".
    :ivar accession: Identifies a record by its accession.  The scope of
        resolution is the entire Archive.
    """
    identifiers: Optional[IdentifierType] = field(
        default=None,
        metadata={
            "name": "IDENTIFIERS",
            "type": "Element",
            "namespace": "",
        }
    )
    refname: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )
    refcenter: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )
    accession: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )
