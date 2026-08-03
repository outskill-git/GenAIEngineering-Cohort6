from sentence_transformers import SentenceTransformer
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import argparse
from typing import List, Optional
from lancedb import connect


def print_section(title: str, width: int = 78) -> None:
    border = "=" * width
    print(f"\n{border}")
    print(f"{title.center(width)}")
    print(border)

# retrieve
def retrieve_with_lancedb(db_path: str, table: str, q_emb: List[float], k: int = 5, label: Optional[int] = None):
    try:
        db = connect(db_path)
        try:
            tbl = db.get_table(table)
        except Exception:
            tbl = db.open_table(table)

        query = tbl.search(q_emb).limit(k)
        if label is not None:
            query = query.where(f"label = {int(label)}")

        # try converting to pandas if available
        try:
            df = query.to_pandas()
            hits = []
            for i, row in df.iterrows():
                score = row.get("score", row.get("_distance"))
                hits.append({"text": row["text"], "label": row.get("label"), "score": score})
            return hits
        except Exception:
            # fallback: try to iterate
            return list(query)
    except Exception as exc:
        print("[warn] LanceDB query failed:", exc)
        return []

# augment
def build_prompt(query: str, contexts: List[str]) -> str:
    prompt_lines = ["You are a helpful assistant. Use the context below to answer the question.", "Context:"]
    for i, c in enumerate(contexts, start=1): # contexts var contains the hits returned by the func above `retrieve_with_lancedb`
        prompt_lines.append(f"[{i}] {c}")
    prompt_lines.append("\nQuestion: " + query)
    prompt_lines.append("Answer:")
    return "\n".join(prompt_lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", type=str, default="./rag_lancedb_db")
    parser.add_argument("--table", type=str, default="ag_news")
    parser.add_argument("--query", type=str, required=True)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--label", type=int, default=None, help="Optional metadata label filter (0..4 for Yelp Review Full)")

    args = parser.parse_args()

    # embedding model
    embed_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    q_emb = embed_model.encode([args.query], convert_to_numpy=True, normalize_embeddings=True)[0]

    print_section("Retrieving from LanceDB (cosine similarity)")
    hits = retrieve_with_lancedb(args.db_path, args.table, q_emb.tolist(), k=args.top_k, label=args.label)

    if not hits:
        print("No hits returned from LanceDB. Exiting.")
        return

    print_section("Top retrieved passages")
    contexts = []
    for rank, hit in enumerate(hits, start=1):
        text = hit.get("text") or hit.get("_source", {}).get("text")
        score = hit.get("score", None)
        label = hit.get("label", None)
        print(f"Rank {rank} | score: {score} | label: {label}")
        print(text)
        print("-" * 78)
        contexts.append(text)

    prompt = build_prompt(args.query, contexts)

    print_section("Prompt sent to generator")
    print(prompt[:2000])

    # generate
    model_name = "google/flan-t5-small"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    inputs = tokenizer(prompt, return_tensors="pt")
    generated = model.generate(**inputs, max_new_tokens=100, do_sample=False)
    out = tokenizer.decode(generated[0], skip_special_tokens=True)

    print_section("Generation")
    print(out)


if __name__ == "__main__":
    main()
