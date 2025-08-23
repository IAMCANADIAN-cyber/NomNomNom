import os
import hashlib
from pathlib import Path
import datetime
import numpy as np
import faiss

from context_distiller.core.db import get_engine, create_tables, get_session, File, Chunk, IndexMapping
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

def ingest_pipeline(folder, db_path='context_distiller.db', index_path='context_distiller.faiss'):
    """
    Orchestrates the ingestion process and builds the search index.
    """
    engine = get_engine(db_path)
    create_tables(engine)
    session = get_session(engine)
    embedding_model = get_embedding_model()

    # --- Step 1: Ingest Files and Create Chunks ---
    for filepath in discover_files(folder):
        content_hash = hash_file(filepath)

        existing_file = session.query(File).filter_by(content_hash=content_hash).first()
        if existing_file:
            print(f"Skipping already ingested file: {filepath}")
            continue

        print(f"Ingesting new file: {filepath}")
        stat = os.stat(filepath)

        text = extract_text(filepath)
        if not text or not text.strip():
            print(f"Skipping file with no extractable text: {filepath}")
            continue

        new_file = File(
            path=str(filepath),
            size_bytes=stat.st_size,
            mtime=datetime.datetime.fromtimestamp(stat.st_mtime),
            content_hash=content_hash,
            status='new',
            extracted_text=text,
        )
        session.add(new_file)
        session.commit() # Commit to get file_id

        chunks = chunk_text(text)
        if not chunks:
            continue

        embeddings = generate_embeddings(chunks, embedding_model)

        for i, chunk_text_content in enumerate(chunks):
            new_chunk = Chunk(
                file_id=new_file.file_id,
                text=chunk_text_content,
                embedding=embeddings[i].tobytes()
            )
            session.add(new_chunk)
        session.commit()

    # --- Step 2: Build/Rebuild the FAISS Index ---
    print("Building FAISS index...")
    all_chunks = session.query(Chunk).order_by(Chunk.chunk_id).all()
    if not all_chunks:
        print("No chunks found to index.")
        return

    # Clear old index mappings
    session.query(IndexMapping).delete()
    session.commit()

    embeddings = np.array([np.frombuffer(chunk.embedding, dtype=np.float32) for chunk in all_chunks])
    dimension = embeddings.shape[1]

    # Using IndexFlatL2, which is good for cosine similarity on normalized embeddings
    index = faiss.IndexFlatL2(dimension)
    faiss.normalize_L2(embeddings) # Normalize for cosine similarity
    index.add(embeddings)

    faiss.write_index(index, index_path)

    # --- Step 3: Create Mappings from Index Position to Chunk ID ---
    for i, chunk in enumerate(all_chunks):
        mapping = IndexMapping(faiss_index=i, chunk_id=chunk.chunk_id)
        session.add(mapping)
    session.commit()

    print(f"FAISS index with {index.ntotal} vectors built and saved to {index_path}")
