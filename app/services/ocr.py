"""
Document parsing: Tesseract OCR for images and pypdf for PDF extraction.
"""

import io
import logging
from typing import List, Optional

from pypdf import PdfReader

logger = logging.getLogger(__name__)


def extract_text_from_pdf(content: bytes) -> str:
    """
    Extract text from a PDF document using pypdf.

    Falls back to OCR per-page when text extraction yields empty results.
    """
    reader = PdfReader(io.BytesIO(content))
    pages: List[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            pages.append(text.strip())
        else:
            ocr_text = _ocr_pdf_page_as_image(content, len(pages))
            if ocr_text:
                pages.append(ocr_text)
    return "\n\n".join(pages)


def extract_text_from_image(content: bytes) -> str:
    """Run Tesseract OCR on a single image buffer."""
    return _run_tesseract(content)


def _ocr_pdf_page_as_image(pdf_content: bytes, page_index: int) -> str:
    """Render a PDF page to image and OCR it (requires pdf2image + poppler)."""
    try:
        from pdf2image import convert_from_bytes

        images = convert_from_bytes(pdf_content, first_page=page_index + 1, last_page=page_index + 1)
        if images:
            buf = io.BytesIO()
            images[0].save(buf, format="PNG")
            return _run_tesseract(buf.getvalue())
    except Exception as exc:
        logger.warning("PDF page OCR failed for page %d: %s", page_index, exc)
    return ""


def _run_tesseract(image_bytes: bytes) -> str:
    """Execute Tesseract OCR on image bytes."""
    try:
        import pytesseract
        from PIL import Image

        image = Image.open(io.BytesIO(image_bytes))
        return pytesseract.image_to_string(image)
    except Exception as exc:
        logger.warning("Tesseract OCR failed: %s", exc)
        return ""


def parse_document(content: bytes, mime_type: str) -> str:
    """
    Route document content to the appropriate parser based on MIME type.

    Args:
        content: Raw file bytes.
        mime_type: Detected MIME type.

    Returns:
        Extracted plain text.
    """
    if mime_type == "application/pdf":
        return extract_text_from_pdf(content)
    if mime_type.startswith("image/"):
        return extract_text_from_image(content)
    if mime_type == "text/plain":
        return content.decode("utf-8", errors="replace")
    return ""
