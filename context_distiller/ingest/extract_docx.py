import docx

def extract_text_from_docx(filepath):
    """
    Extracts text from a DOCX file.
    """
    doc = docx.Document(filepath)
    return "\n".join([para.text for para in doc.paragraphs])
