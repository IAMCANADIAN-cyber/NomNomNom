import os
from pathlib import Path
import pypdf
import docx
from bs4 import BeautifulSoup

def extract_text(filepath: Path) -> str:
    """
    Extracts text from a file, handling different file types.
    """
    file_extension = filepath.suffix.lower()

    try:
        if file_extension == '.txt' or file_extension == '.md':
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()

        elif file_extension == '.pdf':
            text = ""
            with open(filepath, 'rb') as f:
                reader = pypdf.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() or ""
            return text

        elif file_extension == '.docx':
            doc = docx.Document(filepath)
            full_text = []
            for para in doc.paragraphs:
                full_text.append(para.text)
            return '\n'.join(full_text)

        elif file_extension == '.html' or file_extension == '.htm':
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                soup = BeautifulSoup(f, 'html.parser')
                return soup.get_text()

        else:
            # For other file types, attempt to read as text as a fallback.
            # This might handle other simple text-based formats.
            # For binary files, it will likely return junk, but we ignore errors.
            print(f"Warning: Unsupported file type '{file_extension}' for {filepath}. Attempting to read as plain text.")
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()

    except Exception as e:
        print(f"Error processing file {filepath}: {e}")
        return ""
