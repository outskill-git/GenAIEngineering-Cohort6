"""End-to-end hybrid RAG demo with chunking, LanceDB, BM25, and RRF fusion."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Dict, List

import pandas as pd

from bm25 import SimpleBM25
from chunking_strategies import Chunk, document_aware_chunks, recursive_character_chunks, semantic_chunks
from pretty_print import kv, preview, section, step
from simple_embeddings import DEFAULT_HF_EMBEDDING_MODEL, Embedder, make_embedder, tokenize


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DB_DIR = ROOT / "lancedb"


def read_document(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("Install pypdf to read PDFs: pip3 install -r requirements.txt") from exc

        reader = PdfReader(str(path))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    return path.read_text(encoding="utf-8")


def create_demo_pdf(source_md: Path, output_pdf: Path) -> Path:
    """Create a simple PDF from the markdown source if reportlab is available."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    except ImportError as exc:
        raise RuntimeError("Install reportlab to generate the PDF: pip3 install -r requirements.txt") from exc

    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(output_pdf), pagesize=letter)
    story = []
    for raw_line in source_md.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            story.append(Spacer(1, 8))
        elif line.startswith("# "):
            story.append(Paragraph(line[2:], styles["Title"]))
        elif line.startswith("## "):
            story.append(Paragraph(line[3:], styles["Heading2"]))
        else:
            story.append(Paragraph(line, styles["BodyText"]))
    doc.build(story)
    return output_pdf


def explain_strategy(strategy: str) -> str:
    explanations = {
        "document": "Use markdown headings as chunk boundaries. Great when document structure is trustworthy.",
        "recursive": "Try large natural boundaries first, then fall back to smaller ones while keeping overlap.",
        "semantic": "Compare neighboring sentences and split when the local topic changes.",
    }
    return explanations[strategy]


def build_chunks(text: str, strategy: str) -> List[Chunk]:
    if strategy == "document":
        return document_aware_chunks(text)
    if strategy == "recursive":
        return recursive_character_chunks(text, chunk_size=850, overlap=120)
    if strategy == "semantic":
        return semantic_chunks(text, similarity_threshold=0.18)
    raise ValueError(f"Unknown strategy: {strategy}")


def reset_table(db_path: Path, table_name: str) -> None:
    if db_path.exists():
        shutil.rmtree(db_path)


def index_chunks(
    chunks: List[Chunk],
    table_name: str = "hybrid_rag_chunks",
    reset: bool = True,
    embedding_backend: str = "hf",
    embedding_model: str = DEFAULT_HF_EMBEDDING_MODEL,
):
    try:
        import lancedb
    except ImportError as exc:
        raise RuntimeError("Install LanceDB first: pip3 install -r requirements.txt") from exc

    if reset:
        reset_table(DB_DIR, table_name)
    DB_DIR.mkdir(exist_ok=True)

    embedder = make_embedder(backend=embedding_backend, model_name=embedding_model)
    vectors = embedder.encode([chunk.text for chunk in chunks]) # list of embeddings
    rows = []
    for chunk, vector in zip(chunks, vectors):
        rows.append(
            {
                "chunk_id": chunk.chunk_id,
                "text": chunk.text,
                "strategy": chunk.strategy,
                "parent_id": chunk.parent_id or "",
                "heading": (chunk.metadata or {}).get("heading", ""),
                "vector": vector,
            }
        )

    db = lancedb.connect(DB_DIR)
    table = db.create_table(table_name, pd.DataFrame(rows), mode="overwrite")
    return table, rows, embedder


def retrieve_semantic(table, embedder: Embedder, query: str, top_k: int) -> List[Dict[str, object]]:
    query_vector = embedder.encode_one(query)
    result = table.search(query_vector, vector_column_name="vector").limit(top_k).to_pandas()
    records = result.to_dict("records")
    for rank, record in enumerate(records, start=1):
        record["semantic_rank"] = rank
    return records # retrieved records


def retrieve_bm25(rows: List[Dict[str, object]], query: str, top_k: int) -> List[Dict[str, object]]:
    try:
        from rank_bm25 import BM25Okapi

        tokenized = [tokenize(str(row["text"])) for row in rows]
        bm25 = BM25Okapi(tokenized)
        scores = bm25.get_scores(tokenize(query))
    except ImportError:
        bm25 = SimpleBM25(str(row["text"]) for row in rows)
        scores = bm25.get_scores(query)

    ranked = sorted(zip(rows, scores), key=lambda item: item[1], reverse=True)[:top_k]
    records = []
    for rank, (row, score) in enumerate(ranked, start=1):
        record = dict(row)
        record["bm25_score"] = float(score)
        record["bm25_rank"] = rank
        records.append(record)
    return records


def reciprocal_rank_fusion(result_sets: List[List[Dict[str, object]]], k: int = 60, top_k: int = 5) -> List[Dict[str, object]]:
    fused: Dict[str, Dict[str, object]] = {}
    for result_set in result_sets:
        for rank, record in enumerate(result_set, start=1):
            chunk_id = str(record["chunk_id"])
            existing = fused.setdefault(chunk_id, {**record, "rrf_score": 0.0, "sources": []})
            existing["rrf_score"] += 1 / (k + rank)
            if "semantic_rank" in record:
                existing["sources"].append("semantic")
            if "bm25_rank" in record:
                existing["sources"].append("bm25")

    return sorted(fused.values(), key=lambda record: record["rrf_score"], reverse=True)[:top_k]


def answer_with_context(question: str, contexts: List[Dict[str, object]]) -> str:
    """A transparent teaching fallback. Swap this for an LLM call in production."""
    best = contexts[0]["text"] if contexts else "No context found."
    return (
        "Teaching-mode answer: the strongest retrieved passage says: "
        + " ".join(str(best).split()[:55])
        + "..."
    )


def run_demo(
    question: str,
    strategy: str,
    source: Path,
    embedding_backend: str = "hf",
    embedding_model: str = DEFAULT_HF_EMBEDDING_MODEL,
) -> List[Dict[str, object]]:
    section("Hybrid RAG With LanceDB, BM25, And RRF")
    kv("Question", question)
    kv("Chunking strategy", strategy)
    kv("Strategy idea", explain_strategy(strategy))
    kv("Embedding backend", embedding_backend)
    kv("Embedding model", embedding_model if embedding_backend == "hf" else "local hashing vectors")

    step("1. Read the source document")
    text = read_document(source)
    kv("Source", source)
    kv("Characters", len(text))
    kv("Words", len(text.split()))
    preview(text[:420] + "...")

    step("2. Chunk the document")
    chunks = build_chunks(text, strategy)
    kv("Chunks created", len(chunks))
    for chunk in chunks[:3]:
        heading = (chunk.metadata or {}).get("heading", "")
        print(f"\n[{chunk.chunk_id}] {chunk.strategy} {heading}")
        preview(chunk.text[:280] + ("..." if len(chunk.text) > 280 else ""))

    step("3. Embed chunks and store them in LanceDB")
    table, rows, embedder = index_chunks(
        chunks,
        embedding_backend=embedding_backend,
        embedding_model=embedding_model,
    )
    kv("LanceDB path", DB_DIR)
    kv("Table rows", len(rows))
    kv("Vector dimensions", len(rows[0]["vector"]) if rows else 0)

    step("4. Retrieve with semantic vector search")
    semantic = retrieve_semantic(table, embedder, question, top_k=5)
    for record in semantic:
        print(f"{record['semantic_rank']}. {record['chunk_id']} | distance={record.get('_distance', 'n/a')}")
        preview(record["text"], width=78)

    step("5. Retrieve with BM25 keyword search")
    lexical = retrieve_bm25(rows, question, top_k=5)
    for record in lexical:
        print(f"{record['bm25_rank']}. {record['chunk_id']} | bm25_score={record['bm25_score']:.4f}")
        preview(record["text"], width=78)

    step("6. Fuse rankings with reciprocal rank fusion")
    fused = reciprocal_rank_fusion([semantic, lexical], top_k=5)
    for rank, record in enumerate(fused, start=1):
        heading = f" | heading={record.get('heading')}" if record.get("heading") else ""
        print(f"{rank}. {record['chunk_id']} | rrf={record['rrf_score']:.4f} | sources={','.join(record['sources'])}{heading}")
        preview(record["text"], width=78)

    step("7. Build a grounded teaching-mode answer")
    print(answer_with_context(question, fused))
    return fused

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--question", default="When should a logistics escalation be opened for a late order?")
    parser.add_argument("--strategy", choices=["document", "recursive", "semantic"], default="recursive")
    parser.add_argument("--source", type=Path, default=DATA_DIR / "company_ai_handbook.md")
    parser.add_argument("--make-pdf", action="store_true", help="Generate and use a PDF copy of the handbook.")
    parser.add_argument("--embedding-backend", choices=["hf", "hash"], default="hf")
    parser.add_argument("--embedding-model", default=DEFAULT_HF_EMBEDDING_MODEL)
    args = parser.parse_args()

    source = args.source
    if args.make_pdf:
        section("PDF Setup")
        source = create_demo_pdf(DATA_DIR / "company_ai_handbook.md", DATA_DIR / "company_ai_handbook.pdf")
        kv("Generated PDF", source)
    run_demo(
        args.question,
        args.strategy,
        source,
        embedding_backend=args.embedding_backend,
        embedding_model=args.embedding_model,
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[demo error] {exc}", file=sys.stderr)
        raise
