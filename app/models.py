import datetime
from dataclasses import dataclass

from . import db


@dataclass
class ArchiveSubmission(db.Model):
    id = db.Column(db.Integer,
                   primary_key=True)

    dsp_uuid: str = db.Column(db.String(80),
                              unique=True,
                              nullable=True)

    dsp_url: str = db.Column(db.String(80),
                             unique=True,
                             nullable=True)

    created = db.Column(db.DateTime,
                        index=False,
                        unique=False,
                        nullable=False,
                        default=datetime.datetime.utcnow)

    submission = db.relationship('ArchiveEntity',
                                 backref=db.backref('archive_submission', lazy=True))

    file_upload_message: dict = db.Column(db.JSON,
                                          index=False,
                                          unique=False,
                                          nullable=False)

    def __repr__(self):
        return f"<Submission_url: {self.dsp_url}>"

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self):
        db.session.commit()


@dataclass
class ArchiveEntity(db.Model):
    id = db.Column(db.Integer,
                   primary_key=True)

    dsp_uuid: str = db.Column(db.String(80),
                              unique=True,
                              nullable=True)

    dsp_url: str = db.Column(db.String(80),
                             unique=True,
                             nullable=True)

    created = db.Column(db.DateTime,
                        index=False,
                        unique=False,
                        nullable=False,
                        default=datetime.datetime.utcnow)

    converted_data: dict = db.Column(db.JSON,
                                     index=False,
                                     unique=False,
                                     nullable=False)

    derived_from_entities = db.Column(db.JSON,
                                      index=False,
                                      unique=False,
                                      nullable=True)

    submission_id = db.Column(db.Integer,
                              db.ForeignKey('archive_submission.id'),
                              nullable=True)

    type: str = db.Column(db.String(80),
                          unique=True,
                          nullable=False)

    accession: str = db.Column(db.String(80),
                               unique=True,
                               nullable=False)

    def __repr__(self):
        return f"<ArchiveEntity: {self.dsp_url}>"

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self):
        db.session.commit()
