import os
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./genomic_data.db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class AnchorSequence(Base):
    __tablename__ = "anchor_sequences"

    id = Column(String, primary_key=True, index=True)
    sequence_hash = Column(String, unique=True, index=True)
    reference_genome = Column(String, default="GRCh38")
    quality_score = Column(Float)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to diffs
    diffs = relationship("GenomicDifference", back_populates="anchor")


class GenomicDifference(Base):
    __tablename__ = "genomic_differences"

    id = Column(String, primary_key=True, index=True)
    anchor_id = Column(String, ForeignKey("anchor_sequences.id"))
    individual_id = Column(String, index=True)
    position = Column(Integer)
    reference_allele = Column(String)
    alternate_allele = Column(String)
    quality_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to anchor
    anchor = relationship("AnchorSequence", back_populates="diffs")


def create_tables():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
