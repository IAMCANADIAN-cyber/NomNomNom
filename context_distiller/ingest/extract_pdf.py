import PyPDF2

def extract_text_from_pdf(filepath):
    """
    Extracts text from a PDF file.
    """
    with open(filepath, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    return text
