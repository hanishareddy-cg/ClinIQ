from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.session import Base


class Patient(Base):
    __tablename__ = "patients"

    subject_id:   Mapped[int]         = mapped_column(Integer, primary_key=True)
    gender:       Mapped[str | None]  = mapped_column(String(1))
    dob:          Mapped[date | None] = mapped_column(Date)
    dod:          Mapped[date | None] = mapped_column(Date, nullable=True)
    dod_hosp:     Mapped[date | None] = mapped_column(Date, nullable=True)
    expire_flag:  Mapped[int | None]  = mapped_column(Integer)

    admissions:   Mapped[list["Admission"]] = relationship(back_populates="patient")


class Admission(Base):
    __tablename__ = "admissions"

    hadm_id:              Mapped[int]           = mapped_column(Integer, primary_key=True)
    subject_id:           Mapped[int]           = mapped_column(ForeignKey("patients.subject_id"), index=True)
    admittime:            Mapped[datetime | None] = mapped_column(DateTime)
    dischtime:            Mapped[datetime | None] = mapped_column(DateTime)
    admission_type:       Mapped[str | None]    = mapped_column(String(50))
    diagnosis:            Mapped[str | None]    = mapped_column(Text)
    hospital_expire_flag: Mapped[int | None]    = mapped_column(Integer)

    patient: Mapped["Patient"] = relationship(back_populates="admissions")


class Diagnosis(Base):
    __tablename__ = "diagnoses"

    id:          Mapped[int]       = mapped_column(Integer, primary_key=True, autoincrement=True)
    subject_id:  Mapped[int]       = mapped_column(ForeignKey("patients.subject_id"), index=True)
    hadm_id:     Mapped[int]       = mapped_column(ForeignKey("admissions.hadm_id"), index=True)
    icd9_code:   Mapped[str | None] = mapped_column(String(10), index=True)
    short_title: Mapped[str | None] = mapped_column(String(100))
    long_title:  Mapped[str | None] = mapped_column(Text)
    seq_num:     Mapped[int | None] = mapped_column(Integer)  # 1 = primary diagnosis


class Medication(Base):
    __tablename__ = "medications"

    id:               Mapped[int]        = mapped_column(Integer, primary_key=True, autoincrement=True)
    subject_id:       Mapped[int]        = mapped_column(ForeignKey("patients.subject_id"), index=True)
    hadm_id:          Mapped[int]        = mapped_column(ForeignKey("admissions.hadm_id"), index=True)
    drug:             Mapped[str | None] = mapped_column(String(200), index=True)
    drug_type:        Mapped[str | None] = mapped_column(String(50))
    formulary_drug_cd: Mapped[str | None] = mapped_column(String(20))
    dose_val_rx:      Mapped[str | None] = mapped_column(String(50))
    dose_unit_rx:     Mapped[str | None] = mapped_column(String(50))
    route:            Mapped[str | None] = mapped_column(String(50))
    startdate:        Mapped[datetime | None] = mapped_column(DateTime)
    enddate:          Mapped[datetime | None] = mapped_column(DateTime)


class LabResult(Base):
    __tablename__ = "lab_results"

    id:         Mapped[int]         = mapped_column(Integer, primary_key=True, autoincrement=True)
    subject_id: Mapped[int]         = mapped_column(ForeignKey("patients.subject_id"), index=True)
    hadm_id:    Mapped[int | None]  = mapped_column(ForeignKey("admissions.hadm_id"), index=True)
    itemid:     Mapped[int | None]  = mapped_column(Integer, index=True)
    label:      Mapped[str | None]  = mapped_column(String(100))
    charttime:  Mapped[datetime | None] = mapped_column(DateTime, index=True)
    value:      Mapped[str | None]  = mapped_column(String(50))
    valuenum:   Mapped[float | None] = mapped_column(Float)
    valueuom:   Mapped[str | None]  = mapped_column(String(20))
    flag:       Mapped[str | None]  = mapped_column(String(10))  # "abnormal", "delta", None

    __table_args__ = (
        Index("idx_lab_subject_label", "subject_id", "label"),
    )


class Vital(Base):
    __tablename__ = "vitals"

    id:         Mapped[int]          = mapped_column(Integer, primary_key=True, autoincrement=True)
    subject_id: Mapped[int]          = mapped_column(ForeignKey("patients.subject_id"), index=True)
    hadm_id:    Mapped[int | None]   = mapped_column(ForeignKey("admissions.hadm_id"), index=True)
    itemid:     Mapped[int | None]   = mapped_column(Integer)
    label:      Mapped[str | None]   = mapped_column(String(100))
    charttime:  Mapped[datetime | None] = mapped_column(DateTime, index=True)
    valuenum:   Mapped[float | None] = mapped_column(Float)
    valueuom:   Mapped[str | None]   = mapped_column(String(20))


class ClinicalNote(Base):
    __tablename__ = "clinical_notes_meta"

    row_id:      Mapped[int]        = mapped_column(Integer, primary_key=True)
    subject_id:  Mapped[int]        = mapped_column(ForeignKey("patients.subject_id"), index=True)
    hadm_id:     Mapped[int | None] = mapped_column(ForeignKey("admissions.hadm_id"), index=True)
    chartdate:   Mapped[date | None] = mapped_column(Date, index=True)
    category:    Mapped[str | None] = mapped_column(String(50), index=True)
    description: Mapped[str | None] = mapped_column(String(100))
    es_doc_id:   Mapped[str | None] = mapped_column(String(50))  # maps to ES _id

    __table_args__ = (
        Index("idx_notes_meta_category", "subject_id", "category"),
    )
