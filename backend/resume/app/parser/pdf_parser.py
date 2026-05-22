"""PDF text extraction using PyMuPDF."""

import fitz  # PyMuPDF


def extract_text_from_pdf(content: bytes) -> str:
    """Extract text from PDF bytes."""
    text_parts = []
    with fitz.open(stream=content, filetype="pdf") as doc:
        for page in doc:
            text_parts.append(page.get_text())
    return "\n".join(text_parts).strip()
