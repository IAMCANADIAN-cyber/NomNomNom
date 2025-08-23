import nltk

def chunk_text(text: str, target_chunk_size_chars: int = 1000, overlap_sents: int = 2) -> list[str]:
    """
    Splits a text into chunks of a given size, respecting sentence boundaries.

    :param text: The text to chunk.
    :param target_chunk_size_chars: The desired size of each chunk in characters.
    :param overlap_sents: The number of sentences to overlap between chunks.
    :return: A list of text chunks.
    """
    if not text or not text.strip():
        return []

    try:
        # Ensure NLTK tokenizers are downloaded
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('tokenizers/punkt_tab')
    except LookupError:
        print("NLTK tokenizer models not found. Downloading 'punkt' and 'punkt_tab'...")
        nltk.download('punkt')
        nltk.download('punkt_tab')

    sentences = nltk.sent_tokenize(text)

    chunks = []
    current_chunk_sents = []
    current_chunk_len = 0

    for i, sentence in enumerate(sentences):
        # Add sentence to current chunk
        current_chunk_sents.append(sentence)
        current_chunk_len += len(sentence)

        # If the chunk is big enough, finalize it
        if current_chunk_len >= target_chunk_size_chars:
            chunks.append(" ".join(current_chunk_sents))

            # Start the next chunk with an overlap
            overlap_start_index = max(0, len(current_chunk_sents) - overlap_sents)
            current_chunk_sents = current_chunk_sents[overlap_start_index:]
            current_chunk_len = len(" ".join(current_chunk_sents))

    # Add the last remaining chunk if it's not empty
    if current_chunk_sents:
        chunks.append(" ".join(current_chunk_sents))

    return chunks
