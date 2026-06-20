from backend.utils.text_utils import MAX_CHUNK_CHARS, chunk_note, clean_note_text, normalize_date


def test_chunk_note_short_text_returns_single_chunk():
    text = "Patient presented with chest pain."
    chunks = chunk_note(text)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_note_empty_returns_empty():
    assert chunk_note("") == []
    assert chunk_note("   ") == []
    assert chunk_note(None) == []


def test_chunk_note_splits_on_double_newline():
    section_a = "A" * 2000
    section_b = "B" * 2000
    text = section_a + "\n\n" + section_b
    chunks = chunk_note(text)
    assert len(chunks) >= 2
    for chunk in chunks:
        assert len(chunk) <= MAX_CHUNK_CHARS + 50  # small tolerance for overlap


def test_chunk_note_all_chunks_within_limit():
    long_text = "\n\n".join(["Section content " * 50] * 20)
    chunks = chunk_note(long_text)
    for chunk in chunks:
        assert len(chunk) <= MAX_CHUNK_CHARS + 50


def test_chunk_note_preserves_content():
    text = "Important clinical finding: creatinine elevated.\n\nPatient was treated."
    chunks = chunk_note(text)
    combined = " ".join(chunks)
    assert "creatinine elevated" in combined
    assert "Patient was treated" in combined


def test_clean_note_text_removes_control_chars():
    text = "Normal text\x00with\x01null bytes\x02and controls"
    result = clean_note_text(text)
    assert "\x00" not in result
    assert "Normal text" in result


def test_clean_note_text_normalizes_whitespace():
    text = "word1   word2\t\tword3"
    result = clean_note_text(text)
    assert "   " not in result
    assert "\t\t" not in result


def test_clean_note_text_handles_none():
    assert clean_note_text(None) == ""
    assert clean_note_text("") == ""


def test_normalize_date_valid():
    dt = normalize_date("2112-05-16 14:32:00")
    assert dt is not None
    assert dt.year == 2112
    assert dt.month == 5


def test_normalize_date_date_only():
    dt = normalize_date("2112-05-16")
    assert dt is not None
    assert dt.day == 16


def test_normalize_date_null_values():
    assert normalize_date(None) is None
    assert normalize_date("") is None
    assert normalize_date("nan") is None
    assert normalize_date("NaT") is None
