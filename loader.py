from pypdf import PdfReader

# Load the PDF file
reader = PdfReader("chicagoBudget2026.pdf")

# Get the first page
page = reader.pages[0]

# Extract and print the text
print(page.extract_text())
