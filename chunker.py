"""
chunker.py
==========
Responsible for one thing: reading raw .txt files and splitting them
into chunks. No cleaning, no filtering, no deduplication — that is
cleaner.py's job.

Three chunking strategies, selected by subdirectory:

  chunk_review_file()   coursicle/ and rmp/
      One chunk per -----------delimited review block.
      Metadata parsed from the pipe-delimited header line.

  chunk_reddit_file()   reddit/
      Sliding window of ~400 words with 50-word overlap.
      Preserves discussion context across comment boundaries.

  chunk_catalog_file()  official/
      One chunk per -----------delimited course entry.
      Course code extracted from the first line.

Routing table (used by ingest.py):
  SUBDIR_STRATEGY  maps subdirectory name → strategy key
  CHUNKER_MAP      maps strategy key      → chunker function
"""

import re
import hashlib
from pathlib import Path
from typing import Iterator

# ---------------------------------------------------------------------------
# Routing tables  (imported by ingest.py)
# ---------------------------------------------------------------------------

SUBDIR_STRATEGY: dict[str, str] = {
    "coursicle": "review",
    "rmp":       "review",
    "reddit":    "reddit",
    "official":  "catalog",
}

# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _uid(text: str) -> str:
    """
    12-character MD5 hash of the chunk text.
    Deterministic: same text always produces the same ID.
    Used as the deduplication key in ingest.py.
    """
    return hashlib.md5(text.encode()).hexdigest()[:12]


def _word_count(text: str) -> int:
    return len(text.split())


def _parse_review_header(block: str) -> dict:
    """
    Parse the pipe-delimited metadata line that opens every review block.

    Example input (first line of block):
      Professor: Apan Qasem | Course: CS3339 | Quality: 5.0/5 | Difficulty: 4.0/5 | Grade: A | Date: May 10th, 2025

    Returns:
      {"professor": "Apan Qasem", "course": "CS3339", "quality": "5.0/5", ...}

    Missing fields are simply absent from the returned dict — the caller
    adds source_file, source_dir, and chunk_type afterwards.
    """
    meta: dict = {}
    first_line = block.strip().splitlines()[0] if block.strip() else ""
    for pair in first_line.split("|"):
        if ":" in pair:
            key, _, value = pair.partition(":")
            clean_key = key.strip().lower().replace(" ", "_")
            meta[clean_key] = value.strip()
    return meta


# ---------------------------------------------------------------------------
# Chunkers
# ---------------------------------------------------------------------------

def chunk_review_file(path: Path, source_dir: str) -> Iterator[dict]:
    """
    Split a Coursicle or RMP review file into one chunk per review.

    Files use ---------- (5+ dashes) as a separator between reviews.
    Blocks shorter than 5 words are skipped — they are blank separators
    or stray newlines, not real reviews.

    Each yielded chunk:
      {
        "id":       str,   # MD5 hash of text
        "text":     str,   # full block including header line
        "metadata": {
          "professor":   str,
          "course":      str,
          "quality":     str,   # e.g. "5.0/5"  (RMP only)
          "difficulty":  str,   # e.g. "4.0/5"  (RMP only)
          "grade":       str,   # e.g. "A"       (RMP only)
          "date":        str,   # e.g. "May 10th, 2025" (RMP only)
          "source":      str,   # e.g. "Coursicle"      (Coursicle only)
          "year_level":  str,   # e.g. "Senior"         (Coursicle only)
          "major":       str,   # e.g. "CS"             (Coursicle only)
          "source_file": str,   # filename, e.g. "apanqasem.txt"
          "source_dir":  str,   # subdirectory, e.g. "rmp"
          "chunk_type":  "review"
        }
      }
    """
    raw = path.read_text(encoding="utf-8", errors="replace")
    blocks = re.split(r"-{5,}", raw)

    for block in blocks:
        text = block.strip()
        if not text or _word_count(text) < 5:
            continue

        meta = _parse_review_header(text)
        meta["source_file"] = path.name
        meta["source_dir"]  = source_dir
        meta["chunk_type"]  = "review"

        yield {"id": _uid(text), "text": text, "metadata": meta}


def chunk_reddit_file(path: Path, source_dir: str,
                      max_words: int = 400,
                      overlap_words: int = 50) -> Iterator[dict]:
    """
    Split a Reddit thread file into overlapping word-window chunks.

    Reddit threads are conversations — one comment builds on the previous.
    Chunking comment-by-comment would break that context, so instead we:

      1. Split on ---------- to get individual comments.
      2. Flatten all words into one stream, inserting a ||SEP|| marker
         between comments as a soft boundary.
      3. Slide a window of max_words across the stream, advancing by
         (max_words - overlap_words) each step.
      4. Strip ||SEP|| markers from the output text.

    The 50-word overlap means consecutive chunks share their boundary
    words, so a sentence that straddles two chunks isn't lost entirely.

    Each yielded chunk:
      {
        "id":       str,
        "text":     str,   # plain text, no header line
        "metadata": {
          "source_file":  str,
          "source_dir":   str,
          "chunk_type":   "reddit",
          "chunk_index":  int    # 0-based position in the file
        }
      }
    """
    raw = path.read_text(encoding="utf-8", errors="replace")
    comments = [c.strip() for c in re.split(r"-{5,}", raw) if c.strip()]

    words: list[str] = []
    for comment in comments:
        words.extend(comment.split())
        words.append("||SEP||")

    i = 0
    chunk_index = 0
    while i < len(words):
        window = list(words[i: i + max_words])
        if not window:
            break

        # Trim trailing separators so chunks don't end at a boundary marker
        while window and window[-1] == "||SEP||":
            window.pop()

        text = " ".join(w for w in window if w != "||SEP||").strip()
        if text and _word_count(text) >= 10:
            yield {
                "id": _uid(text),
                "text": text,
                "metadata": {
                    "source_file":  path.name,
                    "source_dir":   source_dir,
                    "chunk_type":   "reddit",
                    "chunk_index":  chunk_index,
                },
            }
            chunk_index += 1

        # Slide forward, skipping leading separators at the new position
        i += max(1, max_words - overlap_words)
        while i < len(words) and words[i] == "||SEP||":
            i += 1


def chunk_catalog_file(path: Path, source_dir: str) -> Iterator[dict]:
    """
    Split the TXST course catalog into one chunk per course entry.

    Each entry starts with a line like:
      CS 3354. Software Engineering I.
    followed by the course description and prerequisites.

    The course code (e.g. "CS3354") is extracted from that first line
    and stored in metadata for filtering.

    Each yielded chunk:
      {
        "id":       str,
        "text":     str,
        "metadata": {
          "source_file": str,
          "source_dir":  str,
          "chunk_type":  "catalog",
          "course":      str    # e.g. "CS3354"
        }
      }
    """
    raw = path.read_text(encoding="utf-8", errors="replace")
    entries = re.split(r"-{5,}", raw)

    for entry in entries:
        text = entry.strip()
        if not text or _word_count(text) < 5:
            continue

        first_line = text.splitlines()[0].strip()
        match = re.match(r"(CS\s*\d+\w*)", first_line, re.IGNORECASE)
        course_code = match.group(1).replace(" ", "") if match else "unknown"

        yield {
            "id": _uid(text),
            "text": text,
            "metadata": {
                "source_file": path.name,
                "source_dir":  source_dir,
                "chunk_type":  "catalog",
                "course":      course_code,
            },
        }


# ---------------------------------------------------------------------------
# Dispatcher  (used by ingest.py)
# ---------------------------------------------------------------------------

CHUNKER_MAP: dict[str, callable] = {
    "review":  chunk_review_file,
    "reddit":  chunk_reddit_file,
    "catalog": chunk_catalog_file,
}