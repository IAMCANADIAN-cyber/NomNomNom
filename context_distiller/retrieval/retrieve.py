import numpy as np
import faiss
from context_distiller.core.db import get_engine, get_session, Chunk, IndexMapping
from context_distiller.represent.embeddings import get_embedding_model, generate_embeddings

def retrieve_chunks(query: str, top_k: int = 5, db_path='context_distiller.db', index_path='context_distiller.faiss'):
    """
    Retrieves the most relevant chunks for a given query using a FAISS index.
    """
    engine = get_engine(db_path)
    session = get_session(engine)
    embedding_model = get_embedding_model()

    try:
        index = faiss.read_index(index_path)
    except RuntimeError:
        print(f"Error: FAISS index file not found at '{index_path}'. Please run the ingestion and indexing pipeline first.")
        return []

    # Generate embedding for the query
    query_embedding = generate_embeddings([query], embedding_model)
    faiss.normalize_L2(query_embedding) # Normalize the query vector

    # Search the index
    distances, indices = index.search(query_embedding, top_k)

    if not indices.any():
        return []

    # Get the chunk IDs from the mapping table using the retrieved indices
    top_k_indices = indices[0]
    mappings = session.query(IndexMapping).filter(IndexMapping.faiss_index.in_(top_k_indices.tolist())).all()

    # Create a map from index position to chunk_id
    id_to_chunk_id = {mapping.faiss_index: mapping.chunk_id for mapping in mappings}

    # Fetch the corresponding chunks from the database, preserving the order from FAISS
    ordered_chunk_ids = [id_to_chunk_id.get(idx) for idx in top_k_indices]
    ordered_chunk_ids = [cid for cid in ordered_chunk_ids if cid is not None]

    if not ordered_chunk_ids:
        return []

    chunks = session.query(Chunk).filter(Chunk.chunk_id.in_(ordered_chunk_ids)).all()

    # Reorder chunks to match the similarity order from FAISS
    chunk_map = {chunk.chunk_id: chunk for chunk in chunks}
    ordered_chunks = [chunk_map.get(chunk_id) for chunk_id in ordered_chunk_ids]
    ordered_chunks = [c for c in ordered_chunks if c is not None]

    return ordered_chunks
