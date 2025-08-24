import os
import hashlib
from pathlib import Path
import datetime
import numpy as np
import faiss

from context_distiller.core.db import get_engine, create_tables, get_session, File, Chunk, IndexMapping, Entity, EntityChunkLink
from context_distiller.ingest.extract import extract_text
from context_distiller.represent.chunking import chunk_text
from context_distiller.represent.embeddings import get_embedding_model, generate_embeddings
from context_distiller.represent.entities import get_spacy_model, extract_entities

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
    spacy_model = get_spacy_model()
    local_entity_cache = {} # Cache to prevent duplicate merges in a single session

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

        # Process each chunk for entities
        for i, chunk_text_content in enumerate(chunks):
            new_chunk = Chunk(
                file_id=new_file.file_id,
                text=chunk_text_content,
                embedding=embeddings[i].tobytes()
            )
            session.add(new_chunk)
            session.flush() # Flush to get the chunk_id for the link

            # Extract and store entities for the new chunk
            entities = extract_entities(chunk_text_content, spacy_model)
            links_in_this_chunk = set() # Prevent duplicate links for the same entity in the same chunk
            for ent in entities:
                cache_key = (ent.text, ent.label_)
                if cache_key in local_entity_cache:
                    merged_entity = local_entity_cache[cache_key]
                else:
                    # Use merge to either get the existing entity or create a new one
                    entity_to_store = Entity(text=ent.text, label=ent.label_)
                    merged_entity = session.merge(entity_to_store)
                    session.flush() # Flush to get the entity_id
                    local_entity_cache[cache_key] = merged_entity

                link_key = (merged_entity.entity_id, new_chunk.chunk_id)
                if link_key in links_in_this_chunk:
                    continue

                # Create the link between the chunk and the entity
                link = EntityChunkLink(
                    entity_id=merged_entity.entity_id,
                    chunk_id=new_chunk.chunk_id,
                    start_char=ent.start_char,
                    end_char=ent.end_char
                )
                session.add(link)
                links_in_this_chunk.add(link_key)

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
