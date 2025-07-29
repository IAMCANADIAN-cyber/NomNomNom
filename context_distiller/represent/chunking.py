def chunk_text(text, chunk_size=400, overlap=50):
    """
    Splits a text into chunks of a given size with a given overlap.
    """
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunks.append(text[i:i + chunk_size])
    return chunks
