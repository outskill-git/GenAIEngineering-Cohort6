from sentence_transformers import SentenceTransformer
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import argparse
from typing import List, Optional


def print_section(title: str, width: int = 78) -> None:
    border = "=" * width
    print(f"\n{border}")
    print(f"{title.center(width)}")
    print(border)


def retrieve_chunks(
    db_path: str,
    table: str,
    query_vec: List[float],
    top_k: int = 5,
    label: Optional[int] = None,
):
    from lancedb import connect

    db = connect(db_path)
    try:
        tbl = db.get_table(table)
    except Exception:
        tbl = db.open_table(table)

    q = tbl.search(query_vec).limit(top_k)
    if label is not None:
        q = q.where(f"label = {int(label)}")

    # LanceDB returns `_distance` in this version, older examples use `score`.
    results = q.to_pandas()
    chunks = []
    for _, row in results.iterrows():
        chunks.append(
            {
                "text": row.get("text"),
                "label": row.get("label"),
                "score": row.get("_distance", row.get("score")),
            }
        )
    return chunks


def build_prompt(question: str, contexts: List[str]) -> str:
    lines = [
        "You are a concise QA assistant.",
        "Answer the question using only the context below.",
        "",
        "Context:",
    ]
    for i, ctx in enumerate(contexts, start=1):
        lines.append(f"{i}. {ctx}")
    lines.extend(
        [
            "",
            f"Question: {question}",
            "Answer in one short sentence:",
        ]
    )
    return "\n".join(lines)


def generate_final_answer(question: str, contexts: List[str]) -> str:
    model_name = "google/flan-t5-small"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

    prompt = build_prompt(question, contexts)
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
    out = model.generate(
        **inputs,
        max_new_tokens=80,
        num_beams=4,
        do_sample=False,
        length_penalty=0.8,
    )
    answer = tokenizer.decode(out[0], skip_special_tokens=True).strip()
    return answer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", type=str, default="./rag_lancedb_db")
    parser.add_argument("--table", type=str, default="ag_news")
    parser.add_argument("--query", type=str, required=True, help="Question to answer")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--label", type=int, default=None, help="Optional metadata filter")
    args = parser.parse_args()

    print_section("Loading embedding model")
    embed_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    q_vec = embed_model.encode([args.query], convert_to_numpy=True, normalize_embeddings=True)[0]

    print_section("Retrieving top contexts")
    chunks = retrieve_chunks(args.db_path, args.table, q_vec.tolist(), top_k=args.top_k, label=args.label)
    if not chunks:
        print("No chunks returned from LanceDB. Exiting.")
        return

    for i, c in enumerate(chunks, start=1):
        print(f"{i}. score={c['score']:.4f} | label={c['label']}\n{c['text']}\n")

    contexts = [c["text"] for c in chunks if isinstance(c.get("text"), str)]
    answer = generate_final_answer(args.query, contexts)

    print_section("Final Answer")
    print(answer)


if __name__ == "__main__":
    main()
