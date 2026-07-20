import hashlib
import re
import pdfplumber
from pathlib import Path
from collections import Counter
import re
import json



def load_pdf(path: Path):
    """
    Extract text from a single PDF and return a normalized record.
    Pipiline: extract pages-> strip/headers/footers -> join -> collapes line-wraps-> remove dots
    """

    pages = []

    with pdfplumber.open(path) as pdf:

        for page in pdf.pages:
            
            pages.append(page.extract_text() or "") # "" is for if page is empty(none)
        raw_pages = "\n".join(pages) #raw joined text(no cleaning touches it)
        clean_pages = strip_headers_footers(pages) #Cleans text
        text = "\n".join(clean_pages)
        text = collapse_linewraps(text)
        text = re.sub(r"\.{4,}", " ", text)


    return make_record(path, "pdf", text, metadata={"num_pages": len(pages), "chars_raw": len(raw_pages)})


def make_record(path: Path, fmt: str, text: str, metadata: dict) -> dict:
    """
    Build the record shape for loader
    """
    return {
        "doc_id": hashlib.md5(str(path).encode()).hexdigest()[:12],
        "title": path.stem,
        "source_path": str(path),
        "format": fmt,
        "text": text,
        "metadata": metadata,
    }

def load_corpus(raw_dir="data/raw") -> list[dict]:
    """
    Walk data/raw, load every PDF, and route failures to quarantine
    instead of letting bad file crash the run
    """
    records, quarantined = [], []
    for file in Path(raw_dir).iterdir():
        if not (file.is_file() and file.suffix.lower() == ".pdf"): #skip anything that isn't an actual .pdf file(other formats not supported)
            continue
        try:
            rec = load_pdf(file)
            # A file can extract "successfully" and still be useless -
            # these are our own quality gates, separate from pdfplumber
            # crashing outright.
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
    """
    Detect and remove lines that repeat across most pages by counting how often each edge line appears,
    then dropping anything above a frequency threshold.
    """
    def norm(line):
        # Replace digits with # so "Page 12" and "Page 13" (or any two
        # page numbers) normalize to the same string and get counted
        # together, instead of looking like two different one-off lines.
        return re.sub(r"\d+", "#", line.strip())

    # Pass 1: tally how often each normalized edge line shows up.
    counts = Counter()
    for p in pages:
        lines = p.splitlines()
        for line in lines[:edge] + lines[-edge:]:
            if line.strip():
                counts[norm(line)] += 1

    junk = {l for l, c in counts.items() if c > len(pages) * threshold}
    # Pass 2: rebuild each page keeping only non-junk lines.
    cleaned = []
    for p in pages:
        kept = [ln for ln in p.splitlines() if norm(ln) not in junk]
        cleaned.append("\n".join(kept))
    return cleaned

def collapse_linewraps(text: str) -> str:
    """
    PDF extraction inserts a newline at the end of every visual line,
    chopping sentences mid-thought. Join a line ending in a lowercase
    letter/comma/semicolon to a following line that starts lowercase -
    that pattern means "this is one sentence broken across two lines,"
    not a real paragraph or list break.
    """
    return re.sub(r"(?<=[a-z,;])\n(?=[a-z])", " ", text)

def dedupe(records):
    """
    remove exact-duplicate documents
    """
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


def main():
    # --- run the pipeline ---
    records, quarantined = load_corpus()
    records, dupes = dedupe(records)

    report = {
        "documents_processed": len(records),
        "documents_quarantined": len(quarantined),
        "chars_before_cleaning": sum(r["metadata"]["chars_raw"] for r in records),
        "chars_after_cleaning": sum(len(r["text"]) for r in records),
        "duplicates_removed": dupes,
        "quarantined": quarantined,
    }
    print(json.dumps(report, indent=2))
    Path("data/report.json").write_text(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()