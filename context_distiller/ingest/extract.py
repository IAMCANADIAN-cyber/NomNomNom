def extract_text(filepath):
    """
    Extracts text from a file.
    """
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()
