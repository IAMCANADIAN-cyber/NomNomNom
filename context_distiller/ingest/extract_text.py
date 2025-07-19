from bs4 import BeautifulSoup

def extract_text_from_file(filepath):
    """
    Extracts text from a file, handling .txt, .md, and .html.
    """
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        if filepath.endswith('.html'):
            soup = BeautifulSoup(f, 'html.parser')
            return soup.get_text()
        else:
            return f.read()
