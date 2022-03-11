from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
from xsdata.models.datatype import XmlDate, XmlDateTime
from converter.ena.classes.sra_common import (
    AttributeType,
    LinkType,
    ObjectType,
)


class AddSchema(Enum):
    STUDY = "study"
    EXPERIMENT = "experiment"
    SAMPLE = "sample"
    RUN = "run"
    ANALYSIS = "analysis"
    DATASET = "dataset"
    POLICY = "policy"
    DAC = "dac"
    PROJECT = "project"
    CHECKLIST = "checklist"
    SAMPLE_GROUP = "sampleGroup"


class ModifySchema(Enum):
    STUDY = "study"
    EXPERIMENT = "experiment"
    SAMPLE = "sample"
    RUN = "run"
    ANALYSIS = "analysis"
    DATASET = "dataset"
    POLICY = "policy"
    DAC = "dac"
    PROJECT = "project"
    CHECKLIST = "checklist"
    SAMPLE_GROUP = "sampleGroup"


class ValidateSchema(Enum):
    STUDY = "study"
    EXPERIMENT = "experiment"
    SAMPLE = "sample"
    RUN = "run"
    ANALYSIS = "analysis"
    DATASET = "dataset"
    POLICY = "policy"
    DAC = "dac"
    PROJECT = "project"
    CHECKLIST = "checklist"
    SAMPLE_GROUP = "sampleGroup"


@dataclass
class SubmissionType(ObjectType):
    """
    A Submission type is used to describe an object that contains submission
    actions to be performed by the archive.

    :ivar title: Short text that can be used to define submissions in
        searches or in displays.
    :ivar contacts:
    :ivar actions:
    :ivar submission_links: Archive created links to associated
        submissions.
    :ivar submission_attributes: Archive assigned properties and
        attributes of a SUBMISSION.
    :ivar submission_date: Submitter assigned preparation date of this
        submission object.
    :ivar submission_comment: Submitter assigned comment.
    :ivar lab_name: Laboratory name within submitting institution.
    """
    title: Optional[str] = field(
        default=None,
        metadata={
            "name": "TITLE",
            "type": "Element",
            "namespace": "",
        }
    )
    contacts: Optional["SubmissionType.Contacts"] = field(
        default=None,
        metadata={
            "name": "CONTACTS",
            "type": "Element",
            "namespace": "",
        }
    )
    actions: Optional["SubmissionType.Actions"] = field(
        default=None,
        metadata={
            "name": "ACTIONS",
            "type": "Element",
            "namespace": "",
        }
    )
    submission_links: Optional["SubmissionType.SubmissionLinks"] = field(
        default=None,
        metadata={
            "name": "SUBMISSION_LINKS",
            "type": "Element",
            "namespace": "",
        }
    )
    submission_attributes: Optional["SubmissionType.SubmissionAttributes"] = field(
        default=None,
        metadata={
            "name": "SUBMISSION_ATTRIBUTES",
            "type": "Element",
            "namespace": "",
        }
    )
    submission_date: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )
    submission_comment: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )
    lab_name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )

    @dataclass
    class Contacts:
        contact: List["SubmissionType.Contacts.Contact"] = field(
            default_factory=list,
            metadata={
                "name": "CONTACT",
                "type": "Element",
                "namespace": "",
                "min_occurs": 1,
            }
        )

        @dataclass
        class Contact:
            """
            :ivar name: Name of contact person for this submission.
            :ivar inform_on_status: Internet address of person or
                service to inform on any status changes for this
                submission.
            :ivar inform_on_error: Internet address of person or service
                to inform on any errors for this submission.
            """
            name: Optional[str] = field(
                default=None,
                metadata={
                    "type": "Attribute",
                }
            )
            inform_on_status: Optional[str] = field(
                default=None,
                metadata={
                    "type": "Attribute",
                }
            )
            inform_on_error: Optional[str] = field(
                default=None,
                metadata={
                    "type": "Attribute",
                }
            )

    @dataclass
    class Actions:
        """
        :ivar action: Action to be executed by the archive.
        """
        action: List["SubmissionType.Actions.Action"] = field(
            default_factory=list,
            metadata={
                "name": "ACTION",
                "type": "Element",
                "namespace": "",
                "min_occurs": 1,
            }
        )

        @dataclass
        class Action:
            """
            :ivar add: Add an object to the archive.
            :ivar modify: Modify an object in the archive.
            :ivar cancel: Cancels a private object and its dependent
                objects.
            :ivar suppress: Suppresses a public object and its dependent
                objects.
            :ivar kill: Kills a public object and its dependent objects.
            :ivar hold: Make the object public only when the hold date
                expires.
            :ivar release: The object will be released immediately to
                public.
            :ivar protect: This action is required for data submitted to
                European Genome-Phenome Archive (EGA).
            :ivar rollback: This action will rollback the submission
                from the database
            :ivar validate: Validates the submitted XMLs without
                actually submitting them.
            :ivar receipt: Returns the receipt for a given submission
                alias.
            """
            add: Optional["SubmissionType.Actions.Action.Add"] = field(
                default=None,
                metadata={
                    "name": "ADD",
                    "type": "Element",
                    "namespace": "",
                }
            )
            modify: Optional["SubmissionType.Actions.Action.Modify"] = field(
                default=None,
                metadata={
                    "name": "MODIFY",
                    "type": "Element",
                    "namespace": "",
                }
            )
            cancel: Optional["SubmissionType.Actions.Action.Cancel"] = field(
                default=None,
                metadata={
                    "name": "CANCEL",
                    "type": "Element",
                    "namespace": "",
                }
            )
            suppress: Optional["SubmissionType.Actions.Action.Suppress"] = field(
                default=None,
                metadata={
                    "name": "SUPPRESS",
                    "type": "Element",
                    "namespace": "",
                }
            )
            kill: Optional["SubmissionType.Actions.Action.Kill"] = field(
                default=None,
                metadata={
                    "name": "KILL",
                    "type": "Element",
                    "namespace": "",
                }
            )
            hold: Optional["SubmissionType.Actions.Action.Hold"] = field(
                default=None,
                metadata={
                    "name": "HOLD",
                    "type": "Element",
                    "namespace": "",
                }
            )
            release: Optional["SubmissionType.Actions.Action.Release"] = field(
                default=None,
                metadata={
                    "name": "RELEASE",
                    "type": "Element",
                    "namespace": "",
                }
            )
            protect: Optional[object] = field(
                default=None,
                metadata={
                    "name": "PROTECT",
                    "type": "Element",
                    "namespace": "",
                }
            )
            rollback: Optional[object] = field(
                default=None,
                metadata={
                    "name": "ROLLBACK",
                    "type": "Element",
                    "namespace": "",
                }
            )
            validate: Optional["SubmissionType.Actions.Action.Validate"] = field(
                default=None,
                metadata={
                    "name": "VALIDATE",
                    "type": "Element",
                    "namespace": "",
                }
            )
            receipt: Optional["SubmissionType.Actions.Action.Receipt"] = field(
                default=None,
                metadata={
                    "name": "RECEIPT",
                    "type": "Element",
                    "namespace": "",
                }
            )

            @dataclass
            class Add:
                """
                :ivar source: Filename or relative path to the XML file
                    being submitted.
                :ivar schema: The type of the XML file being submitted.
                """
                source: Optional[str] = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                    }
                )
                schema: Optional[AddSchema] = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                    }
                )

            @dataclass
            class Modify:
                """
                :ivar source: Filename or relative path to the XML file
                    being updated.
                :ivar schema: The type of the XML file being updated.
                """
                source: Optional[str] = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                    }
                )
                schema: Optional[ModifySchema] = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                    }
                )

            @dataclass
            class Cancel:
                """
                :ivar target: Accession or refname of the object that is
                    being cancelled.
                """
                target: Optional[str] = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "required": True,
                    }
                )

            @dataclass
            class Suppress:
                """
                :ivar target: Accession or refname of the object that is
                    being suppressed.
                :ivar hold_until_date: The date when a temporarily
                    suppressed object will be made public.
                """
                target: Optional[str] = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "required": True,
                    }
                )
                hold_until_date: Optional[XmlDate] = field(
                    default=None,
                    metadata={
                        "name": "HoldUntilDate",
                        "type": "Attribute",
                    }
                )

            @dataclass
            class Kill:
                """
                :ivar target: Accession or refname of the object that is
                    being killed.
                :ivar hold_until_date: The date when a temporarily
                    killed object will be made public.
                """
                target: Optional[str] = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "required": True,
                    }
                )
                hold_until_date: Optional[XmlDate] = field(
                    default=None,
                    metadata={
                        "name": "HoldUntilDate",
                        "type": "Attribute",
                    }
                )

            @dataclass
            class Hold:
                """
                :ivar target: Accession or refname of the object that is
                    being made public when the hold date expires. If not
                    specified then all objects in the submission will be
                    assigned the hold date.
                :ivar hold_until_date: The date when the submission will
                    be made public.
                """
                target: Optional[str] = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                    }
                )
                hold_until_date: Optional[XmlDate] = field(
                    default=None,
                    metadata={
                        "name": "HoldUntilDate",
                        "type": "Attribute",
                    }
                )

            @dataclass
            class Release:
                """
                :ivar target: Accession or refname of the object that is
                    made public. If not specified then all objects in
                    the submission will made public.
                """
                target: Optional[str] = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                    }
                )

            @dataclass
            class Validate:
                """
                :ivar source: Filename or relative path to the XML file
                    being validated.
                :ivar schema: The type of the XML file being validated.
                """
                source: Optional[str] = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                    }
                )
                schema: Optional[ValidateSchema] = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                    }
                )

            @dataclass
            class Receipt:
                """
                :ivar target: Submission alias.
                """
                target: Optional[str] = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                    }
                )

    @dataclass
    class SubmissionLinks:
        submission_link: List[LinkType] = field(
            default_factory=list,
            metadata={
                "name": "SUBMISSION_LINK",
                "type": "Element",
                "namespace": "",
                "min_occurs": 1,
            }
        )

    @dataclass
    class SubmissionAttributes:
        submission_attribute: List[AttributeType] = field(
            default_factory=list,
            metadata={
                "name": "SUBMISSION_ATTRIBUTE",
                "type": "Element",
                "namespace": "",
                "min_occurs": 1,
            }
        )


@dataclass
class Submission(SubmissionType):
    class Meta:
        name = "SUBMISSION"


@dataclass
class SubmissionSetType:
    submission: List[SubmissionType] = field(
        default_factory=list,
        metadata={
            "name": "SUBMISSION",
            "type": "Element",
            "namespace": "",
            "min_occurs": 1,
        }
    )


@dataclass
class SubmissionSet(SubmissionSetType):
    """
    An SUBMISSION_SET is a container for a set of studies and a common
    namespace.
    """
    class Meta:
        name = "SUBMISSION_SET"
