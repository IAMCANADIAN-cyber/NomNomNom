import os
import hashlib
from pathlib import Path
import datetime
from context_distiller.core.db import get_engine, create_tables, get_session, File, Chunk
from context_distiller.ingest.extract import extract_text
from context_distiller.represent.chunking import chunk_text
from context_distiller.represent.embeddings import get_embedding_model, generate_embeddings

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
    embedding_model = get_embedding_model()

    for filepath in discover_files(folder):
        content_hash = hash_file(filepath)

        # Check if the file is already in the database
        existing_file = session.query(File).filter_by(content_hash=content_hash).first()
        if existing_file:
            print(f"Skipping already ingested file: {filepath}")
            continue

        print(f"Ingesting new file: {filepath}")
        stat = os.stat(filepath)

        # Extract text
        text = extract_text(filepath)

        new_file = File(
            path=str(filepath),
            size_bytes=stat.st_size,
            mtime=datetime.datetime.fromtimestamp(stat.st_mtime),
            content_hash=content_hash,
            status='new',
            extracted_text=text,
        )
        session.add(new_file)
        session.commit()

        # Chunk text
        chunks = chunk_text(text)

        # Generate embeddings
        embeddings = generate_embeddings(chunks, embedding_model)

        for i, chunk_text_content in enumerate(chunks):
            new_chunk = Chunk(
                file_id=new_file.file_id,
                text=chunk_text_content,
                embedding=embeddings[i].tobytes()
            )
            session.add(new_chunk)
        session.commit()
