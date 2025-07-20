import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from context_distiller.core.db import get_engine, get_session, Chunk
from context_distiller.represent.embeddings import get_embedding_model, generate_embeddings

def retrieve_chunks(query, top_k=5):
    """
    Retrieves the most relevant chunks for a given query.
    """
    engine = get_engine()
    session = get_session(engine)
    embedding_model = get_embedding_model()

    query_embedding = generate_embeddings([query], embedding_model)[0]

    chunks = session.query(Chunk).all()

    chunk_embeddings = np.array([np.frombuffer(chunk.embedding, dtype=np.float32) for chunk in chunks])

    similarities = cosine_similarity([query_embedding], chunk_embeddings)[0]

    top_k_indices = similarities.argsort()[-top_k:][::-1]

    return [chunks[i] for i in top_k_indices]
