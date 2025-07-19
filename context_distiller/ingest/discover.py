import os
import hashlib
from pathlib import Path

def discover_files(start_path):
    """
    Discovers all files in a directory, skipping nothing.
    """
    for root, _, files in os.walk(start_path):
        for file in files:
            yield Path(root) / file

def hash_file(filepath):
    """
    Computes the SHA256 hash of a file.
    """
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while True:
            # Reading is buffered, so we can read in chunks.
            chunk = f.read(h.block_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()
