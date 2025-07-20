import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, LargeBinary, JSON, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

class File(Base):
    __tablename__ = 'files'
    file_id = Column(Integer, primary_key=True)
    path = Column(String, unique=True)
    type = Column(String)
    subtype = Column(String)
    size_bytes = Column(Integer)
    mtime = Column(DateTime)
    content_hash = Column(String, unique=True)
    status = Column(String)
    meta_json = Column(JSON)
    extracted_text = Column(Text)

class Chunk(Base):
    __tablename__ = 'chunks'
    chunk_id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey('files.file_id'))
    modality = Column(String)
    level = Column(Integer, default=0)
    token_len = Column(Integer)
    text = Column(Text)
    meta_json = Column(JSON)
    embedding = Column(LargeBinary)

def get_engine(db_path='context_distiller.db'):
    return create_engine(f'sqlite:///{db_path}')

def create_tables(engine):
    Base.metadata.create_all(engine)

def get_session(engine):
    Session = sessionmaker(bind=engine)
    return Session()
