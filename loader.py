import hashlib
import re
import pdfplumber
from pathlib import Path





def load_pdf(file):
    # Open the PDF and extract text
    with pdfplumber.open(file) as pdf:
        full_text = ""
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"

    # 1. Collapse single line breaks (preceded/followed by characters) into a space
    cleaned_text = re.sub(r'(?<!\n)\n(?!\n)', ' ', full_text)

    # 2. Fix multiple spaces caused by collapsed lines
    cleaned_text = re.sub(r' {2,}', ' ', cleaned_text)

    # 3. Clean up any trailing spaces before a newline
    cleaned_text = re.sub(r' \n', '\n', cleaned_text)
    print(cleaned_text)

    return cleaned_text


def make_record(path: Path, fmt: str, text: str, metadata: dict) -> dict:
    return {
        "doc_id": hashlib.md5(str(path).encode()).hexdigest()[:12],
        "title": path.stem,
        "source_path": str(path),
        "format": fmt,
        "text": text,
        "metadata": metadata,
    }



# Loops through files in the specified directory, skipping subfolders
for file in Path("/Users/daniel/Desktop/Retrieval-Augmented-Generation-Project/data/raw").iterdir():
    
    if file.is_file():
        file_type = file.name[-4:]
        if file_type == '.pdf':
            load_pdf("/Users/daniel/Desktop/Retrieval-Augmented-Generation-Project/data/raw/"+file.name)


