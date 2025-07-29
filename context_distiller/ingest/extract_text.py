from bs4 import BeautifulSoup

def extract_text_from_file(filepath):
    """
    Extracts text from a file, handling .txt, .md, and .html.
    """
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        if filepath.endswith('.html'):
            soup = BeautifulSoup(f, 'html.parser')
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()
            # Get text
            text = soup.get_text()
            # Break into lines and remove leading and trailing space on each
            lines = (line.strip() for line in text.splitlines())
            # Break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            # Drop blank lines
            text = '\n'.join(chunk for chunk in chunks if chunk)
            return text
        else:
            return f.read()
