#!/usr/bin/env python3
"""build_index.py — Pre-build the RAG faiss index from ops_agent/*.md.

Uses the bge-large-en-v1.5 ONNX model via onnxruntime — **no torch**, runs on
any platform with onnxruntime installed. The intent is:

  * **Run this on the Mac before flying** so the index file is on the SSD.
  * On the GB10, agent.py just ``faiss.read_index`` — zero embedding compute.

Output:

  ``SSD_ROOT/rag_index.faiss``   IndexFlatIP, L2-normalized 1024-d vectors
  ``SSD_ROOT/rag_chunks.json``   {"chunks": [...], "meta": [...]}

Configuration via env vars (all optional):

  SSD_ROOT              default auto-detected
  CHUNK_MIN_LEN         default 80     (skip too-short paragraphs)
  CHUNK_MAX_LEN         default 1200   (further split very long paragraphs)
  EMBED_BATCH_SIZE      default 8

Usage:

    pip install onnxruntime tokenizers faiss-cpu numpy
    python build_index.py
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Iterable

import numpy as np


def _detect_ssd_root() -> Path:
    env = os.environ.get("SSD_ROOT")
    if env:
        return Path(env)
    for candidate in (
        Path("/Volumes/SSD-3/Hackathon"),
        Path("/mnt/ssd/Hackathon"),
        Path(__file__).resolve().parent,
    ):
        if (candidate / "models" / "bge-large-en-v1.5").exists():
            return candidate
    raise RuntimeError(
        "Could not locate the SSD bundle. Set SSD_ROOT env var to the directory "
        "containing models/, mock_data/."
    )


SSD_ROOT = _detect_ssd_root()
BGE_DIR = SSD_ROOT / "models" / "bge-large-en-v1.5"
ONNX_PATH = BGE_DIR / "onnx" / "model.onnx"
TOK_PATH = BGE_DIR / "tokenizer.json"
DOCS_DIR = SSD_ROOT / "mock_data" / "ops_agent"
INDEX_OUT = SSD_ROOT / "rag_index.faiss"
CHUNKS_OUT = SSD_ROOT / "rag_chunks.json"

CHUNK_MIN_LEN = int(os.environ.get("CHUNK_MIN_LEN", "80"))
CHUNK_MAX_LEN = int(os.environ.get("CHUNK_MAX_LEN", "1200"))
EMBED_BATCH_SIZE = int(os.environ.get("EMBED_BATCH_SIZE", "8"))


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------


def _split_long(paragraph: str, max_len: int) -> Iterable[str]:
    """Split a paragraph that's longer than ``max_len`` into roughly equal pieces."""
    if len(paragraph) <= max_len:
        yield paragraph
        return
    # Split on sentence boundaries, then greedily pack into <= max_len blocks
    sentences = re.split(r"(?<=[.!?])\s+", paragraph)
    buf = ""
    for sentence in sentences:
        if not buf:
            buf = sentence
        elif len(buf) + 1 + len(sentence) <= max_len:
            buf = f"{buf} {sentence}"
        else:
            yield buf
            buf = sentence
    if buf:
        yield buf


def _chunk_document(text: str) -> list[str]:
    """Split a markdown doc into paragraph-ish chunks."""
    raw_paragraphs = re.split(r"\n\s*\n", text)
    out: list[str] = []
    for paragraph in raw_paragraphs:
        cleaned = paragraph.strip()
        if len(cleaned) < CHUNK_MIN_LEN:
            continue
        out.extend(_split_long(cleaned, CHUNK_MAX_LEN))
    return out


# ---------------------------------------------------------------------------
# Embedding
# ---------------------------------------------------------------------------


def _load_session():
    try:
        import onnxruntime as ort
        from tokenizers import Tokenizer
    except ImportError as exc:
        sys.exit(
            "Missing dependency: " + str(exc) +
            "\n  pip install onnxruntime tokenizers faiss-cpu numpy"
        )
    if not ONNX_PATH.exists():
        sys.exit(f"ONNX model not found at {ONNX_PATH}")
    if not TOK_PATH.exists():
        sys.exit(f"Tokenizer not found at {TOK_PATH}")
    tok = Tokenizer.from_file(str(TOK_PATH))
    sess = ort.InferenceSession(
        str(ONNX_PATH), providers=["CPUExecutionProvider"]
    )
    return tok, sess


def _embed_batch(tok, sess, batch: list[str]) -> np.ndarray:
    encodings = [tok.encode(t) for t in batch]
    # Truncate to BGE's max position (512); pad to max length in batch
    max_len = min(512, max(len(e.ids) for e in encodings))
    input_ids = np.zeros((len(batch), max_len), dtype=np.int64)
    attn_mask = np.zeros((len(batch), max_len), dtype=np.int64)
    for i, enc in enumerate(encodings):
        n = min(len(enc.ids), max_len)
        input_ids[i, :n] = enc.ids[:n]
        attn_mask[i, :n] = enc.attention_mask[:n]
    token_type_ids = np.zeros_like(input_ids)

    feed = {
        "input_ids": input_ids,
        "attention_mask": attn_mask,
        "token_type_ids": token_type_ids,
    }
    expected = {i.name for i in sess.get_inputs()}
    feed = {k: v for k, v in feed.items() if k in expected}

    outputs = sess.run(None, feed)
    # bge convention: [CLS] pooling = output[0][:, 0, :]
    cls = outputs[0][:, 0, :]
    norms = np.linalg.norm(cls, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    return (cls / norms).astype(np.float32)


def embed(tok, sess, texts: list[str]) -> np.ndarray:
    out: list[np.ndarray] = []
    for i in range(0, len(texts), EMBED_BATCH_SIZE):
        batch = texts[i : i + EMBED_BATCH_SIZE]
        out.append(_embed_batch(tok, sess, batch))
        print(
            f"  embedded {min(i + EMBED_BATCH_SIZE, len(texts))}/{len(texts)}",
            flush=True,
        )
    return np.concatenate(out, axis=0)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    try:
        import faiss
    except ImportError:
        sys.exit("Missing faiss. `pip install faiss-cpu`")

    print(f"SSD_ROOT = {SSD_ROOT}")
    print(f"docs    = {DOCS_DIR}")
    print(f"onnx    = {ONNX_PATH}")
    print(f"out idx = {INDEX_OUT}")
    print(f"out json = {CHUNKS_OUT}")

    # Filter out macOS AppleDouble metadata files (`._*`) that exFAT-mounted SSDs surface
    md_files = sorted(p for p in DOCS_DIR.glob("*.md") if not p.name.startswith("._"))
    if not md_files:
        sys.exit(f"No .md files found in {DOCS_DIR}")

    chunks: list[str] = []
    meta: list[dict] = []
    for md in md_files:
        doc_chunks = _chunk_document(md.read_text(encoding="utf-8"))
        for i, chunk in enumerate(doc_chunks):
            chunks.append(chunk)
            meta.append({"source": md.name, "chunk_index": i})
        print(f"  {md.name}: {len(doc_chunks)} chunks")

    if not chunks:
        sys.exit("No chunks produced — check CHUNK_MIN_LEN setting.")

    print(f"\nTotal chunks: {len(chunks)}")
    print("Loading bge-large-en-v1.5 ONNX session ...")
    tok, sess = _load_session()

    print("Embedding ...")
    vectors = embed(tok, sess, chunks)
    print(f"vectors shape: {vectors.shape}")

    print("Building faiss IndexFlatIP ...")
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)

    print(f"Writing {INDEX_OUT} ...")
    faiss.write_index(index, str(INDEX_OUT))
    CHUNKS_OUT.write_text(
        json.dumps({"chunks": chunks, "meta": meta}, ensure_ascii=False, indent=2)
    )
    print(f"Writing {CHUNKS_OUT} ...")

    print("\nDone. Smoke test:")
    q = "How do I reset my password if VPN is failing with VPN-503?"
    qv = embed(tok, sess, [q])
    distances, indices = index.search(qv, 3)
    for rank, (idx, score) in enumerate(zip(indices[0], distances[0])):
        if idx < 0:
            continue
        print(
            f"  #{rank + 1} [{meta[idx]['source']} #{meta[idx]['chunk_index']}] "
            f"score={score:.3f}"
        )
        print(f"     {chunks[idx][:160]}")


if __name__ == "__main__":
    main()
