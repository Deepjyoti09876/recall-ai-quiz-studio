"""Extract plain text from uploaded study material (PDF, DOCX, PPTX, TXT, MD)."""
from io import BytesIO
from pypdf import PdfReader
from docx import Document
from pptx import Presentation


def _pdf(data: bytes) -> str:
    return "\n".join((p.extract_text() or "") for p in PdfReader(BytesIO(data)).pages)


def _docx(data: bytes) -> str:
    return "\n".join(p.text for p in Document(BytesIO(data)).paragraphs)


def _pptx(data: bytes) -> str:
    lines = []
    for slide in Presentation(BytesIO(data)).slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                lines.append(shape.text_frame.text)
    return "\n".join(lines)


def extract_text(name: str, data: bytes) -> str:
    ext = name.lower().rsplit(".", 1)[-1]
    if ext == "pdf":
        return _pdf(data)
    if ext == "docx":
        return _docx(data)
    if ext == "pptx":
        return _pptx(data)
    if ext in ("txt", "md"):
        return data.decode("utf-8", errors="ignore")
    raise ValueError(f"Unsupported file type: .{ext}")
