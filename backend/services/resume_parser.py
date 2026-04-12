"""Resume parser: extract text from PDF/DOCX, then structured data via Claude."""

import io
import json
import re
from pathlib import Path

import anthropic

from backend.config import CLAUDE_MODEL

EXTRACT_SCHEMA = """{
  "skills": ["<string>", ...],
  "projects": [
    {"name": "<string>", "tech": ["<string>", ...], "bullets": ["<string>", ...]}
  ],
  "experience": [
    {"role": "<string>", "company": "<string>", "duration": "<string>", "bullets": ["<string>", ...]}
  ],
  "education": [
    {"degree": "<string>", "institution": "<string>", "graduation": "<string>", "gpa": "<string or null>"}
  ],
  "certifications": ["<string>", ...]
}"""


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF file."""
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(file_bytes))
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    return "\n\n".join(pages)


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from a DOCX file."""
    from docx import Document

    doc = Document(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def extract_text(file_bytes: bytes, filename: str) -> str:
    """Extract text from a resume file based on extension."""
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_bytes)
    elif ext in (".docx", ".doc"):
        return extract_text_from_docx(file_bytes)
    elif ext == ".txt":
        return file_bytes.decode("utf-8", errors="replace")
    else:
        raise ValueError(f"Unsupported file format: {ext}. Accepted: .pdf, .docx, .txt")


def parse_resume(file_bytes: bytes, filename: str) -> dict:
    """Extract text from file, then call Claude to parse into structured data."""
    raw_text = extract_text(file_bytes, filename)

    if not raw_text.strip():
        raise ValueError("Resume file appears to be empty or unreadable")

    client = anthropic.Anthropic()

    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=2048,
        system=(
            "You are a resume parser. Extract structured data from the resume text. "
            "Return ONLY valid JSON matching this schema, no fences, no commentary:\n"
            f"{EXTRACT_SCHEMA}\n\n"
            "Rules:\n"
            "- skills: all technical and soft skills mentioned\n"
            "- projects: personal/academic/professional projects with tech stack and key bullets\n"
            "- experience: work history with role, company, duration, and achievement bullets\n"
            "- education: degrees with institution, graduation date, GPA if listed\n"
            "- certifications: any certifications or professional credentials"
        ),
        messages=[{"role": "user", "content": f"Resume text:\n\n{raw_text[:5000]}"}],
    )

    text = message.content[0].text
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        result = json.loads(match.group(0))
    else:
        result = json.loads(text)

    # Ensure all keys exist
    for key in ["skills", "projects", "experience", "education", "certifications"]:
        if key not in result:
            result[key] = []

    result["raw_text"] = raw_text

    return result
