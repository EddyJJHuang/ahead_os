#!/usr/bin/env python3
"""build_pm_index.py — Pre-build the PM launch-readiness FAISS index.

This mirrors ``build_index.py`` but reads PM Agent docs and playbooks.
Before indexing, it regenerates ``docs/pm_workspace.md`` from the raw PM data
files when they are present:

  ``SSD_ROOT/mock_data/pm_agent/raw/*.json|*.md|*.txt``
  ``SSD_ROOT/mock_data/pm_agent/live/*.json|*.md|*.txt``  (optional private data)
  ``SSD_ROOT/mock_data/pm_agent/docs/*.md``
  ``SSD_ROOT/mock_data/pm_agent/playbook/*.md``

Output:

  ``SSD_ROOT/pm_rag_index.faiss``   IndexFlatIP, L2-normalized vectors
  ``SSD_ROOT/pm_rag_chunks.json``   {"chunks": [...], "meta": [...]}
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Iterable


def _detect_ssd_root() -> Path:
    env = os.environ.get("SSD_ROOT")
    if env:
        return Path(env)
    for candidate in (
        Path("/Volumes/SSD-3/Hackathon"),
        Path("/mnt/ssd/Hackathon"),
        Path(__file__).resolve().parent,
    ):
        if (candidate / "mock_data" / "pm_agent").exists():
            return candidate
    raise RuntimeError(
        "Could not locate the PM bundle. Set SSD_ROOT env var to the directory "
        "containing models/ and mock_data/pm_agent/."
    )


SSD_ROOT = _detect_ssd_root()
BGE_DIR = SSD_ROOT / "models" / "bge-large-en-v1.5"
ONNX_PATH = BGE_DIR / "onnx" / "model.onnx"
TOK_PATH = BGE_DIR / "tokenizer.json"
PM_RAW_DIR = SSD_ROOT / "mock_data" / "pm_agent" / "raw"
PM_LIVE_DIR = SSD_ROOT / "mock_data" / "pm_agent" / "live"
PM_DOCS_DIR = SSD_ROOT / "mock_data" / "pm_agent" / "docs"
PM_PLAYBOOK_DIR = SSD_ROOT / "mock_data" / "pm_agent" / "playbook"
PM_WORKSPACE_DOC = PM_DOCS_DIR / "pm_workspace.md"
INDEX_OUT = SSD_ROOT / "pm_rag_index.faiss"
CHUNKS_OUT = SSD_ROOT / "pm_rag_chunks.json"

CHUNK_MIN_LEN = int(os.environ.get("CHUNK_MIN_LEN", "80"))
CHUNK_MAX_LEN = int(os.environ.get("CHUNK_MAX_LEN", "1200"))
EMBED_BATCH_SIZE = int(os.environ.get("EMBED_BATCH_SIZE", "8"))

PM_RAW_FILES = [
    "calender.json",
    "customers.json",
    "emails.json",
    "github.json",
    "jira.json",
    "notes.md",
    "product_docs.md",
    "sample_expected_brief.txt",
    "slack.json",
    "tasks.json",
]


def _split_long(paragraph: str, max_len: int) -> Iterable[str]:
    if len(paragraph) <= max_len:
        yield paragraph
        return
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
    raw_paragraphs = re.split(r"\n\s*\n", text)
    out: list[str] = []
    for paragraph in raw_paragraphs:
        cleaned = paragraph.strip()
        if len(cleaned) < CHUNK_MIN_LEN:
            continue
        out.extend(_split_long(cleaned, CHUNK_MAX_LEN))
    return out


def _compact_json_value(value) -> str:
    if isinstance(value, dict):
        parts = []
        for key, item in value.items():
            if isinstance(item, (dict, list)):
                parts.append(f"{key}: {_compact_json_value(item)}")
            else:
                parts.append(f"{key}: {item}")
        return "; ".join(parts)
    if isinstance(value, list):
        return " | ".join(_compact_json_value(item) for item in value)
    return str(value)


def _raw_json_to_markdown(path: Path) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    title = path.stem.replace("_", " ").title()
    lines = [f"## {title}", ""]
    if isinstance(data, list):
        for i, item in enumerate(data, start=1):
            lines.append(f"- Item {i}: {_compact_json_value(item)}")
    elif isinstance(data, dict):
        for key, value in data.items():
            lines.append(f"- {key}: {_compact_json_value(value)}")
    else:
        lines.append(str(data))
    return "\n".join(lines)


def _raw_text_to_markdown(path: Path) -> str:
    title = path.stem.replace("_", " ").title()
    text = path.read_text(encoding="utf-8").strip()
    if path.suffix == ".md":
        return text
    return f"## {title}\n\n{text}"


def regenerate_pm_workspace() -> list[str]:
    """Generate docs/pm_workspace.md from fake data plus optional live data."""
    PM_DOCS_DIR.mkdir(parents=True, exist_ok=True)
    sections = [
        "# Generated PM Workspace Snapshot",
        "",
        "Generated from `mock_data/pm_agent/raw/` and optional private "
        "`mock_data/pm_agent/live/` for local PM launch-readiness retrieval.",
        "",
    ]
    missing: list[str] = []
    for filename in PM_RAW_FILES:
        path = PM_RAW_DIR / filename
        if not path.exists():
            missing.append(filename)
            continue
        try:
            if path.suffix == ".json":
                sections.append(_raw_json_to_markdown(path))
            elif path.suffix in {".md", ".txt"}:
                sections.append(_raw_text_to_markdown(path))
            else:
                continue
            sections.append("")
        except (OSError, json.JSONDecodeError) as exc:
            sections.append(f"## {filename}")
            sections.append("")
            sections.append(f"Could not parse {filename}: {type(exc).__name__}: {exc}")
            sections.append("")
    if PM_LIVE_DIR.exists():
        live_files = sorted(
            p for p in PM_LIVE_DIR.iterdir()
            if p.suffix in {".json", ".md", ".txt"} and not p.name.startswith("._")
        )
        if live_files:
            sections.append("# Private Live Workspace Data")
            sections.append("")
        for path in live_files:
            try:
                if path.suffix == ".json":
                    sections.append(_raw_json_to_markdown(path))
                else:
                    sections.append(_raw_text_to_markdown(path))
                sections.append("")
            except (OSError, json.JSONDecodeError) as exc:
                sections.append(f"## {path.name}")
                sections.append("")
                sections.append(f"Could not parse {path.name}: {type(exc).__name__}: {exc}")
                sections.append("")
    if missing:
        sections.append("## Missing Raw Files")
        sections.append("")
        sections.append(
            "These optional Drive fake-data files were not present when the workspace "
            "snapshot was generated: " + ", ".join(missing) + "."
        )
        sections.append("")
    PM_WORKSPACE_DOC.write_text("\n".join(sections).strip() + "\n", encoding="utf-8")
    return missing


def _load_session():
    try:
        import numpy as np
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
    sess = ort.InferenceSession(str(ONNX_PATH), providers=["CPUExecutionProvider"])
    return tok, sess


def _embed_batch(tok, sess, batch: list[str]):
    import numpy as np

    encodings = [tok.encode(t) for t in batch]
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
    cls = outputs[0][:, 0, :]
    norms = np.linalg.norm(cls, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    return (cls / norms).astype(np.float32)


def embed(tok, sess, texts: list[str]):
    import numpy as np

    out = []
    for i in range(0, len(texts), EMBED_BATCH_SIZE):
        batch = texts[i : i + EMBED_BATCH_SIZE]
        out.append(_embed_batch(tok, sess, batch))
        print(
            f"  embedded {min(i + EMBED_BATCH_SIZE, len(texts))}/{len(texts)}",
            flush=True,
        )
    return np.concatenate(out, axis=0)


def _pm_markdown_files() -> list[Path]:
    roots = (PM_DOCS_DIR, PM_PLAYBOOK_DIR)
    files: list[Path] = []
    for root in roots:
        files.extend(p for p in root.glob("*.md") if not p.name.startswith("._"))
    return sorted(files)


def main() -> None:
    print(f"SSD_ROOT = {SSD_ROOT}")
    print(f"raw      = {PM_RAW_DIR}")
    print(f"live     = {PM_LIVE_DIR}")
    print(f"docs     = {PM_DOCS_DIR}")
    print(f"playbook = {PM_PLAYBOOK_DIR}")
    print(f"onnx     = {ONNX_PATH}")
    print(f"out idx  = {INDEX_OUT}")
    print(f"out json = {CHUNKS_OUT}")

    missing_raw = regenerate_pm_workspace()
    if missing_raw:
        print("missing optional raw files: " + ", ".join(missing_raw))

    md_files = _pm_markdown_files()
    if not md_files:
        sys.exit(f"No PM .md files found in {PM_DOCS_DIR} or {PM_PLAYBOOK_DIR}")

    chunks: list[str] = []
    meta: list[dict] = []
    for md in md_files:
        doc_chunks = _chunk_document(md.read_text(encoding="utf-8"))
        rel = md.relative_to(SSD_ROOT)
        for i, chunk in enumerate(doc_chunks):
            chunks.append(chunk)
            meta.append({"source": str(rel), "chunk_index": i})
        print(f"  {rel}: {len(doc_chunks)} chunks")

    if not chunks:
        sys.exit("No chunks produced — check CHUNK_MIN_LEN setting.")

    try:
        import faiss
    except ImportError:
        sys.exit("Missing faiss. `pip install faiss-cpu`")

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
    q = "Should we launch 2026.06 with Acme billing export still at risk?"
    qv = embed(tok, sess, [q])
    distances, indices = index.search(qv, 5)
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
