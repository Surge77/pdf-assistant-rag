LIGATURE_MAP = str.maketrans(
    {
        "ﬁ": "fi",
        "ﬂ": "fl",
        "ﬀ": "ff",
        "ﬃ": "ffi",
        "ﬄ": "ffl",
        "\u00a0": " ",
    }
)


def normalize_text(text: str) -> str:
    return " ".join(text.translate(LIGATURE_MAP).split()).strip()


def _overlap_words(words: list[str], chunk_overlap: int) -> list[str]:
    overlap: list[str] = []
    current_length = 0

    for word in reversed(words):
        additional_length = len(word) if current_length == 0 else len(word) + 1
        if current_length + additional_length > chunk_overlap and overlap:
            break
        overlap.insert(0, word)
        current_length += additional_length

    return overlap


def chunk_text(text: str, chunk_size: int = 800, chunk_overlap: int = 120) -> list[str]:
    cleaned = normalize_text(text)
    if not cleaned:
        return []

    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    words = cleaned.split()
    chunks: list[str] = []
    current_words: list[str] = []
    current_length = 0

    for word in words:
        candidate_length = len(word) if current_length == 0 else current_length + len(word) + 1
        if candidate_length > chunk_size and current_words:
            chunks.append(" ".join(current_words))
            current_words = _overlap_words(current_words, chunk_overlap)
            current_length = len(" ".join(current_words))

        current_words.append(word)
        current_length = len(" ".join(current_words))

    if current_words:
        chunks.append(" ".join(current_words))

    return chunks


def chunk_pages(
    page_texts: list[str],
    chunk_size: int = 800,
    chunk_overlap: int = 120,
) -> list[dict[str, int | str]]:
    chunk_records: list[dict[str, int | str]] = []
    chunk_index = 0

    for page_number, page_text in enumerate(page_texts, start=1):
        for chunk in chunk_text(page_text, chunk_size=chunk_size, chunk_overlap=chunk_overlap):
            chunk_records.append(
                {
                    "page_number": page_number,
                    "chunk_index": chunk_index,
                    "text": chunk,
                }
            )
            chunk_index += 1

    return chunk_records
