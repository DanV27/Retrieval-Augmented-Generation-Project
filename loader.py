import hashlib
import re
import pdfplumber
from pathlib import Path





def load_pdf(path: Path):
    # Open the PDF and extract text

    pages = []

    with pdfplumber.open(path) as pdf:

        for page in pdf.pages:
            pages.append(page.extract_text() or "") # "" is for if page is empty(none)
        text = "\n".join(pages)


    return make_record(path, "pdf", text, metadata={"num_pages": len(pages)})


def make_record(path: Path, fmt: str, text: str, metadata: dict) -> dict:
    return {
        "doc_id": hashlib.md5(str(path).encode()).hexdigest()[:12],
        "title": path.stem,
        "source_path": str(path),
        "format": fmt,
        "text": text,
        "metadata": metadata,
    }

def load_corpus(raw_dir="data/raw") -> list[dict]:
    records = []
    for file in Path(raw_dir).iterdir():
        if file.is_file() and file.suffix.lower() == ".pdf":
            records.append(load_pdf(file))
    return records


records = load_corpus()
print(f"Loaded {len(records)} documents")
if records:
    r = records[0]
    print(r["doc_id"], "|", r["title"], "|", r["metadata"]["num_pages"], "pages")
    print(r["text"][:1500])