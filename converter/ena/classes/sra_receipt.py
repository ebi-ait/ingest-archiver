from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
from xsdata.models.datatype import XmlDate, XmlDateTime


class ExtIdType(Enum):
    STUDY = "study"
    EXPERIMENT = "experiment"
    SAMPLE = "sample"
    SAMPLE_GROUP = "sampleGroup"
    RUN = "run"
    ANALYSIS = "analysis"
    DATASET = "dataset"
    POLICY = "policy"
    DAC = "dac"
    ARRAY_EXPRESS = "ArrayExpress"
    LOCUS_TAG_PREFIX = "LocusTagPrefix"
    TAXON = "Taxon"
    PROJECT = "Project"
    CHECKLIST = "checklist"
    BIOSAMPLE = "biosample"


class IdStatus(Enum):
    DRAFT = "DRAFT"
    PRIVATE = "PRIVATE"
    CANCELLED = "CANCELLED"
    PUBLIC = "PUBLIC"
    SUPPRESSED = "SUPPRESSED"
    KILLED = "KILLED"
    TEMPORARY_SUPPRESSED = "TEMPORARY_SUPPRESSED"
    TEMPORARY_KILLED = "TEMPORARY_KILLED"


class ReceiptActions(Enum):
    ADD = "ADD"
    MODIFY = "MODIFY"
    RELEASE = "RELEASE"
    HOLD = "HOLD"
    VALIDATE = "VALIDATE"
    PROTECT = "PROTECT"
    RECEIPT = "RECEIPT"
    ROLLBACK = "ROLLBACK"


@dataclass
class Id:
    """
    :ivar ext_id: The REF identifies the reference of that object .
    :ivar accession:
    :ivar alias:
    :ivar hold_until_date:
    :ivar status:
    """
    class Meta:
        name = "ID"

    ext_id: List["Id.ExtId"] = field(
        default_factory=list,
        metadata={
            "name": "EXT_ID",
            "type": "Element",
            "namespace": "",
            "nillable": True,
        }
    )
    accession: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )
    alias: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        }
    )
    hold_until_date: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "holdUntilDate",
            "type": "Attribute",
        }
    )
    status: Optional[IdStatus] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )

    @dataclass
    class ExtId:
        accession: Optional[str] = field(
            default=None,
            metadata={
                "type": "Attribute",
                "min_length": 1,
                "max_length": 1024,
            }
        )
        type: Optional[ExtIdType] = field(
            default=None,
            metadata={
                "type": "Attribute",
            }
        )


@dataclass
class Receipt:
    class Meta:
        name = "RECEIPT"

    analysis: List[Id] = field(
        default_factory=list,
        metadata={
            "name": "ANALYSIS",
            "type": "Element",
            "namespace": "",
        }
    )
    experiment: List[Id] = field(
        default_factory=list,
        metadata={
            "name": "EXPERIMENT",
            "type": "Element",
            "namespace": "",
        }
    )
    run: List[Id] = field(
        default_factory=list,
        metadata={
            "name": "RUN",
            "type": "Element",
            "namespace": "",
        }
    )
    sample: List[Id] = field(
        default_factory=list,
        metadata={
            "name": "SAMPLE",
            "type": "Element",
            "namespace": "",
        }
    )
    samplegroup: List[Id] = field(
        default_factory=list,
        metadata={
            "name": "SAMPLEGROUP",
            "type": "Element",
            "namespace": "",
        }
    )
    study: List[Id] = field(
        default_factory=list,
        metadata={
            "name": "STUDY",
            "type": "Element",
            "namespace": "",
        }
    )
    dac: List[Id] = field(
        default_factory=list,
        metadata={
            "name": "DAC",
            "type": "Element",
            "namespace": "",
        }
    )
    policy: List[Id] = field(
        default_factory=list,
        metadata={
            "name": "POLICY",
            "type": "Element",
            "namespace": "",
        }
    )
    dataset: List[Id] = field(
        default_factory=list,
        metadata={
            "name": "DATASET",
            "type": "Element",
            "namespace": "",
        }
    )
    project: List[Id] = field(
        default_factory=list,
        metadata={
            "name": "PROJECT",
            "type": "Element",
            "namespace": "",
        }
    )
    checklist: List[Id] = field(
        default_factory=list,
        metadata={
            "name": "CHECKLIST",
            "type": "Element",
            "namespace": "",
        }
    )
    submission: Optional[Id] = field(
        default=None,
        metadata={
            "name": "SUBMISSION",
            "type": "Element",
            "namespace": "",
        }
    )
    messages: Optional["Receipt.Messages"] = field(
        default=None,
        metadata={
            "name": "MESSAGES",
            "type": "Element",
            "namespace": "",
        }
    )
    actions: List[ReceiptActions] = field(
        default_factory=list,
        metadata={
            "name": "ACTIONS",
            "type": "Element",
            "namespace": "",
            "min_occurs": 1,
        }
    )
    success: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        }
    )
    receipt_date: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "name": "receiptDate",
            "type": "Attribute",
            "required": True,
        }
    )
    submission_file: Optional[str] = field(
        default=None,
        metadata={
            "name": "submissionFile",
            "type": "Attribute",
            "required": True,
            "pattern": r".+\.xml",
        }
    )

    @dataclass
    class Messages:
        error: List[str] = field(
            default_factory=list,
            metadata={
                "name": "ERROR",
                "type": "Element",
                "namespace": "",
            }
        )
        info: List[str] = field(
            default_factory=list,
            metadata={
                "name": "INFO",
                "type": "Element",
                "namespace": "",
            }
        )
