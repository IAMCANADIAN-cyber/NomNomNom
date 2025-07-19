import os
import hashlib
from pathlib import Path
import datetime
from context_distiller.core.db import get_engine, create_tables, get_session, File

def discover_files(start_path):
    """
    Discovers all files in a directory, skipping nothing.
    """
    for root, _, files in os.walk(start_path):
        for file in files:
            yield Path(root) / file

def hash_file(filepath):
    """
    Computes the SHA256 hash of a file.
    """
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while True:
            # Reading is buffered, so we can read in chunks.
            chunk = f.read(h.block_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def ingest_pipeline(folder):
    """
    Orchestrates the ingestion process.
    """
    engine = get_engine()
    create_tables(engine)
    session = get_session(engine)

    for filepath in discover_files(folder):
        content_hash = hash_file(filepath)

        # Check if the file is already in the database
        existing_file = session.query(File).filter_by(content_hash=content_hash).first()
        if existing_file:
            print(f"Skipping already ingested file: {filepath}")
            continue

        print(f"Ingesting new file: {filepath}")
        stat = os.stat(filepath)
        new_file = File(
            path=str(filepath),
            size_bytes=stat.st_size,
            mtime=datetime.datetime.fromtimestamp(stat.st_mtime),
            content_hash=content_hash,
            status='new',
        )
        session.add(new_file)
        session.commit()
