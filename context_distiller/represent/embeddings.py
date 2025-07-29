from sentence_transformers import SentenceTransformer

def get_embedding_model(model_name="all-MiniLM-L6-v2"):
    """
    Loads a sentence-transformer model.
    """
    return SentenceTransformer(model_name)

def generate_embeddings(chunks, model):
    """
    Generates embeddings for a list of text chunks.
    """
    return model.encode(chunks)
