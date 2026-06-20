import re
from datetime import datetime

# Approximate: 4 chars ≈ 1 token. Max 800 tokens = 3200 chars per chunk.
MAX_CHUNK_CHARS = 3200
OVERLAP_CHARS = 400


def chunk_note(text: str) -> list[str]:
    """
    Split a clinical note into chunks at section boundaries.
    Splits on double-newline first, then merges small sections and splits
    oversized ones. Returns a list of chunk strings.
    """
    if not text or not text.strip():
        return []

    text = text.strip()

    if len(text) <= MAX_CHUNK_CHARS:
        return [text]

    # Split on double-newline (section boundaries in MIMIC notes)
    sections = [s.strip() for s in re.split(r"\n\n+", text) if s.strip()]

    chunks: list[str] = []
    current = ""

    for section in sections:
        candidate = (current + "\n\n" + section).strip() if current else section

        if len(candidate) <= MAX_CHUNK_CHARS:
            current = candidate
        else:
            # Save current chunk with overlap carried into next
            if current:
                chunks.append(current)
                # carry last OVERLAP_CHARS as context into the next chunk
                overlap = current[-OVERLAP_CHARS:] if len(current) > OVERLAP_CHARS else current
                current = overlap + "\n\n" + section
            else:
                # single section too large — hard split at word boundary
                for hard_chunk in _hard_split(section):
                    chunks.append(hard_chunk)
                current = ""

    if current:
        chunks.append(current)

    return chunks


def _hard_split(text: str) -> list[str]:
    chunks = []
    while len(text) > MAX_CHUNK_CHARS:
        split_at = text.rfind(" ", 0, MAX_CHUNK_CHARS)
        if split_at == -1:
            split_at = MAX_CHUNK_CHARS
        chunks.append(text[:split_at].strip())
        text = text[split_at:].strip()
    if text:
        chunks.append(text)
    return chunks


def normalize_date(value: str | None) -> datetime | None:
    if not value or str(value).strip().lower() in ("", "nan", "nat", "none"):
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(value).strip(), fmt)
        except ValueError:
            continue
    return None


def clean_note_text(text: str | None) -> str:
    if not text:
        return ""
    # Remove non-printable characters except newlines and tabs
    text = re.sub(r"[^\x09\x0A\x0D\x20-\x7E]", " ", str(text))
    # Collapse excessive whitespace within lines
    text = re.sub(r"[ \t]{2,}", " ", text)
    # Normalize line endings
    text = re.sub(r"\r\n?", "\n", text)
    # Collapse >3 consecutive newlines
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip()
