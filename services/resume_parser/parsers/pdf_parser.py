"""PDF resume parser using PyMuPDF."""

import fitz  # PyMuPDF


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text content from a PDF file."""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text_parts = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text_parts.append(page.get_text())

    doc.close()
    return "\n".join(text_parts).strip()
