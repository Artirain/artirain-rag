import os
import glob

from pypdf import PdfReader

from .config import Config
from .store import Store


def read_file(path):
    if path.lower().endswith(".pdf"):
        reader = PdfReader(path)
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def chunk_text(text, size, overlap):
    text = text.strip()
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = end - overlap
    return [c for c in chunks if c]


def collect_chunks(cfg: Config):
    chunks = []
    patterns = ("*.md", "*.txt", "*.pdf")
    paths = []
    for pat in patterns:
        paths.extend(glob.glob(os.path.join(cfg.data_dir, "**", pat), recursive=True))
    for path in sorted(set(paths)):
        text = read_file(path)
        source = os.path.relpath(path, cfg.data_dir)
        for c in chunk_text(text, cfg.chunk_size, cfg.chunk_overlap):
            chunks.append({"text": c, "source": source})
    return chunks


def ingest(cfg: Config):
    store = Store(cfg)
    store.reset()
    chunks = collect_chunks(cfg)
    n = store.upsert(chunks) if chunks else 0
    return n
