"""
cleaner.py
==========
Responsible for one thing: taking a list of raw chunks produced by
chunker.py and making them safe and balanced for embedding.

Five cleaning passes, applied in order by clean_chunks():

  Pass 1  _pass_junk_filter       Drop chunks that are scraper noise
  Pass 2  _pass_truncation_flag   Flag chunks that end mid-sentence
  Pass 3  _pass_short_flag        Flag chunks under 50 words
  Pass 4  _pass_fill_missing_date Fill missing date fields with "unknown"
  Pass 5  _pass_professor_cap     Trim overrepresented professors to 100
                                  reviews, keeping the most diverse ones

Each pass returns the (possibly modified) chunk list and writes a
summary into the shared `report` dict.  clean_chunks() collects all
five reports and returns them together so the caller can print them.

No file I/O happens here.  This module is purely in-memory transforms.
"""

import warnings

# Maximum reviews kept per professor before diversity selection kicks in.
MAX_REVIEWS_PER_PROF = 100

# Words that should never appear in a genuine student review body.
# All entries are lowercase; comparison is done with body.lower().
JUNK_SIGNALS = [
    "nvidia",
    "wwdc",
    "macos",
    "apple",
    "image slip",
    "tagline",
    "bill that comes",
]


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _body(text: str) -> str:
    """
    Return everything after the first (header) line of a review block.

    Review blocks look like:
      Professor: ... | Course: ... | ...      ← header line
                                               ← blank line
      The actual review text starts here.     ← body

    For catalog and reddit chunks there is no header, so the whole
    text is returned as-is.
    """
    parts = text.split("\n\n", 1)
    return parts[1].strip() if len(parts) > 1 else text.strip()


def _word_count(text: str) -> int:
    return len(text.split())


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def clean_chunks(chunks: list[dict]) -> tuple[list[dict], dict]:
    """
    Run all five cleaning passes in sequence.

    Parameters
    ----------
    chunks : list[dict]
        Raw chunks from chunker.py, after content-hash deduplication.

    Returns
    -------
    cleaned : list[dict]
        The cleaned chunk list.  Some chunks are dropped (Pass 1),
        some are modified in-place (Passes 2-4), some are removed and
        replaced with a smaller diverse subset (Pass 5).

    report : dict
        Human-readable summary of what each pass did.  Keys:
          "junk_dropped"       int
          "junk_examples"      list[str]   up to 5 dropped chunk previews
          "truncated_flagged"  int
          "short_flagged"      int
          "date_filled"        int
          "professor_cap"      dict | str  per-professor before/after counts,
                                           or a string if sklearn was missing
    """
    report: dict = {}
    chunks = _pass_junk_filter(chunks, report)
    chunks = _pass_truncation_flag(chunks, report)
    chunks = _pass_short_flag(chunks, report)
    chunks = _pass_fill_missing_date(chunks, report)
    chunks = _pass_professor_cap(chunks, report)
    return chunks, report


# ---------------------------------------------------------------------------
# Pass 1 — Junk filter
# ---------------------------------------------------------------------------

def _pass_junk_filter(chunks: list[dict], report: dict) -> list[dict]:
    """
    Drop review chunks that are scraper noise rather than real reviews.

    Two conditions trigger a drop (either is sufficient):
      1. Body is fewer than 16 words — too short to be a real review.
      2. Body contains a known junk signal keyword (see JUNK_SIGNALS).

    Non-review chunks (reddit, catalog) are passed through unchanged
    because their structure is different and doesn't produce this noise.

    Why 16 words?
      The Nvidia headline that slipped through the original 15-word
      threshold was exactly 15 words, so the threshold was raised by one.
      The keyword blocklist catches any future headlines regardless of length.
    """
    kept: list[dict] = []
    dropped: list[str] = []

    for chunk in chunks:
        if chunk["metadata"].get("chunk_type") != "review":
            kept.append(chunk)
            continue

        body = _body(chunk["text"])
        body_lower = body.lower()
        is_junk_keyword = any(signal in body_lower for signal in JUNK_SIGNALS)

        if _word_count(body) < 16 or is_junk_keyword:
            dropped.append(chunk["text"][:80])
        else:
            kept.append(chunk)

    report["junk_dropped"]   = len(dropped)
    report["junk_examples"]  = dropped[:5]
    return kept


# ---------------------------------------------------------------------------
# Pass 2 — Truncation flag
# ---------------------------------------------------------------------------

def _pass_truncation_flag(chunks: list[dict], report: dict) -> list[dict]:
    """
    Flag review chunks that appear to be truncated at scrape time.

    A chunk is considered possibly truncated if its body does not end
    with sentence-ending punctuation: . ! ? " '

    Truncated chunks are KEPT — they contain real partial information —
    but marked so the generation prompt can say "do not speculate about
    incomplete reviews."

    Adds to metadata:  "possibly_truncated": True
    """
    flagged = 0
    for chunk in chunks:
        if chunk["metadata"].get("chunk_type") != "review":
            continue
        body = _body(chunk["text"])
        if body and body[-1] not in ".!?\"'":
            chunk["metadata"]["possibly_truncated"] = True
            flagged += 1

    report["truncated_flagged"] = flagged
    return chunks


# ---------------------------------------------------------------------------
# Pass 3 — Short review flag
# ---------------------------------------------------------------------------

def _pass_short_flag(chunks: list[dict], report: dict) -> list[dict]:
    """
    Flag review chunks whose body is fewer than 50 words.

    These are genuine reviews, just brief ("Awful teacher. Deserves to
    be fired").  They are KEPT because even a 4-word review carries
    clear sentiment, but flagged so downstream code can optionally
    exclude them from retrieval if embedding quality is a concern.

    Adds to metadata:  "short_review": True
    """
    flagged = 0
    for chunk in chunks:
        if chunk["metadata"].get("chunk_type") != "review":
            continue
        body = _body(chunk["text"])
        if _word_count(body) < 50:
            chunk["metadata"]["short_review"] = True
            flagged += 1

    report["short_flagged"] = flagged
    return chunks


# ---------------------------------------------------------------------------
# Pass 4 — Fill missing date
# ---------------------------------------------------------------------------

def _pass_fill_missing_date(chunks: list[dict], report: dict) -> list[dict]:
    """
    Fill in a "date" field for review chunks that don't have one.

    Coursicle reviews use a "Source: Coursicle" field instead of a date,
    so their headers produce no "date" key.  Without this pass, any
    downstream code that accesses chunk["metadata"]["date"] would crash
    with a KeyError on Coursicle chunks.

    Fills missing dates with the string "unknown" rather than None so
    ChromaDB metadata filters (which require strings) don't break.
    """
    filled = 0
    for chunk in chunks:
        if chunk["metadata"].get("chunk_type") == "review":
            if not chunk["metadata"].get("date"):
                chunk["metadata"]["date"] = "unknown"
                filled += 1

    report["date_filled"] = filled
    return chunks


# ---------------------------------------------------------------------------
# Pass 5 — Professor cap (diversity-aware)
# ---------------------------------------------------------------------------

def _pass_professor_cap(chunks: list[dict], report: dict,
                         max_per_prof: int = MAX_REVIEWS_PER_PROF) -> list[dict]:
    """
    Trim professors with more than max_per_prof reviews to exactly
    max_per_prof, selecting the most topically diverse subset.

    Why cap?
      Gholoom had 315 chunks, Li had 12.  Without a cap, vague queries
      return Gholoom-dominated results purely due to volume, not relevance.

    Why diversity selection instead of random sampling?
      Random sampling might keep 100 near-identical "hard class, take it"
      reviews while discarding the one review that mentions office hours
      or the grading curve.  Diversity selection maximises topic coverage.

    Algorithm — greedy max-margin:
      1. TF-IDF-vectorise all review bodies for that professor.
      2. Compute the full (n × n) cosine similarity matrix.
      3. Seed with the review that has the lowest mean similarity to all
         others — the most "unique" one.
      4. Repeatedly select the review most dissimilar to any already-
         selected review (minimise the maximum similarity to the set).
      5. Stop when max_per_prof reviews are selected.

    TF-IDF vs sentence-transformers:
      sentence-transformers would give better semantic similarity but
      was unavailable in this build environment.  TF-IDF works well here
      because reviews are short and keyword-heavy (exam, curve, project,
      office hours).  To upgrade: replace TfidfVectorizer with
      SentenceTransformer("all-MiniLM-L6-v2").encode() and compute
      cosine similarity the same way.

    Requires:  pip install scikit-learn numpy
    Falls back gracefully if sklearn is not installed (skips the cap).
    """
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np
    except ImportError:
        report["professor_cap"] = "SKIPPED — run: pip install scikit-learn numpy"
        return chunks

    review_chunks = [c for c in chunks if c["metadata"].get("chunk_type") == "review"]
    other_chunks  = [c for c in chunks if c["metadata"].get("chunk_type") != "review"]

    # Group by professor
    by_prof: dict[str, list[dict]] = {}
    for chunk in review_chunks:
        prof = chunk["metadata"].get("professor", "unknown")
        by_prof.setdefault(prof, []).append(chunk)

    capped_details: dict = {}
    final_reviews: list[dict] = []

    for prof, prof_chunks in by_prof.items():
        if len(prof_chunks) <= max_per_prof:
            final_reviews.extend(prof_chunks)
            continue

        # Vectorise review bodies
        texts = [_body(c["text"]) for c in prof_chunks]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            vec       = TfidfVectorizer(stop_words="english", min_df=1)
            tfidf     = vec.fit_transform(texts)

        sim_matrix = cosine_similarity(tfidf)       # shape (n, n), values 0–1

        selected: list[int] = []
        remaining = set(range(len(prof_chunks)))

        # Seed: most unique review (lowest average similarity to all others)
        seed = int(sim_matrix.mean(axis=1).argmin())
        selected.append(seed)
        remaining.remove(seed)

        # Greedy expansion
        while len(selected) < max_per_prof and remaining:
            remaining_list = list(remaining)
            # For each candidate, how similar is it to the closest selected review?
            max_sim = np.array([
                sim_matrix[i, selected].max() for i in remaining_list
            ])
            # Pick the candidate furthest from everything already selected
            chosen = remaining_list[int(max_sim.argmin())]
            selected.append(chosen)
            remaining.remove(chosen)

        kept = [prof_chunks[i] for i in selected]
        final_reviews.extend(kept)
        capped_details[prof] = {"before": len(prof_chunks), "after": len(kept)}

    report["professor_cap"] = capped_details
    return other_chunks + final_reviews