import hashlib
import re
import pdfplumber
from pathlib import Path
from collections import Counter
import re




def load_pdf(path: Path):
    # Open the PDF and extract text

    pages = []

    with pdfplumber.open(path) as pdf:

        for page in pdf.pages:
            pages.append(page.extract_text() or "") # "" is for if page is empty(none)
        clean_pages = strip_headers_footers(pages)
        text = "\n".join(clean_pages)


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


def strip_headers_footers(pages: list[str], edge=4, threshold=0.4) -> list[str]:
    def norm(line):
        return re.sub(r"\d+", "#", line.strip())

    counts = Counter()
    for p in pages:
        lines = p.splitlines()
        for line in lines[:edge] + lines[-edge:]:
            if line.strip():
                counts[norm(line)] += 1

    junk = {l for l, c in counts.items() if c > len(pages) * threshold}

    cleaned = []
    for p in pages:
        kept = [ln for ln in p.splitlines() if norm(ln) not in junk]
        cleaned.append("\n".join(kept))
    return cleaned


records = load_corpus()
print(f"Loaded {len(records)} documents")
if records:
    r = records[0]
    print(r["doc_id"], "|", r["title"], "|", r["metadata"]["num_pages"], "pages")
    print(r["text"][:1500])

    print(r["text"][50000:52000])   # somewhere in the body
    print("=" * 60)
    print(r["text"][150000:152000]) # somewhere later