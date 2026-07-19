import re
import pdfplumber

# Open the PDF and extract text
with pdfplumber.open("chicagoBudget2026.pdf") as pdf:
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

print(cleaned_text.strip())