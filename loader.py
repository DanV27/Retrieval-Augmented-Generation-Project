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
        text = collapse_linewraps(text)
        text = re.sub(r"\.{4,}", " ", text)


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
    records, quarantined = [], []
    for file in Path(raw_dir).iterdir():
        if not file.is_file() and file.suffix.lower() == ".pdf":
            continue
        try:
            rec = load_pdf(file)
            if len(rec["text"].strip()) < 100:        # empty/near-empty
                raise ValueError("extracted text too short")
            if rec["text"].count("�") > 50:           # encoding garbage
                raise ValueError("encoding garbage detected")
            records.append(rec)
        except Exception as e:
            print(f"[quarantine] {file.name}: {e}")
            quarantined.append({"file": str(file), "reason": str(e)})

    return records, quarantined


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

def collapse_linewraps(text: str) -> str:
    return re.sub(r"(?<=[a-z,;])\n(?=[a-z])", " ", text)

def dedupe(records):
    seen, unique, dupes = {}, [], 0
    for r in records:
        fingerprint = hashlib.md5(
            re.sub(r"\s+", " ", r["text"].lower()).encode()).hexdigest() #compute this doc's signature
        if fingerprint in seen: #Have we already store this signature?
            dupes += 1 #Yes, dont keep it, count it
        else:
            seen[fingerprint] = r["doc_id"] #NO, remember for next time
            unique.append(r) #and keep this document
    return unique, dupes #return the unique ones and dupe tally



records, quarantined = load_corpus()
print(f"Loaded {len(records)} documents")
print(f"Quarantined {len(quarantined)} documents")

records, dupes = dedupe(records)
print(f"Duplicates removed: {dupes}")

if records:
    r = records[0]
    print(r["doc_id"], "|", r["title"], "|", r["metadata"]["num_pages"], "pages")
    print(r["text"][:1500])