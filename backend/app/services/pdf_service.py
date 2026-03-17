from io import BytesIO

from pypdf import PdfReader

from app.services.chunk_service import normalize_text


def extract_pages_from_pdf_bytes(file_bytes: bytes) -> list[str]:
    reader = PdfReader(BytesIO(file_bytes))
    page_text: list[str] = []

    for page in reader.pages:
        extracted_text = page.extract_text() or ""
        page_text.append(normalize_text(extracted_text))

    return page_text


def extract_text_from_pdf_bytes(file_bytes: bytes) -> tuple[str, int]:
    page_text = extract_pages_from_pdf_bytes(file_bytes)
    return "\n".join(page_text).strip(), len(page_text)
