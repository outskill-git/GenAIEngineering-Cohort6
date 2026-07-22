from datasets import load_dataset
from sentence_transformers import SentenceTransformer
import argparse
import numpy as np
import pandas as pd
from tqdm.auto import tqdm
from lancedb import connect

def print_section(title: str, width: int = 78) -> None:
    border = "=" * width
    print(f"\n{border}")
    print(f"{title.center(width)}")
    print(border)


def build_and_store(db_path: str, table_name: str, documents, labels, embeddings):
    try:
        print_section("Connecting to LanceDB and storing vectors")
        db = connect(db_path) # init the db instance
        df = pd.DataFrame({"text": documents, "label": labels})
        # lancedb can accept a column of python lists as embeddings
        df["embedding"] = list(embeddings)

        try:
            # Newer LanceDB versions may infer vector column automatically, older versions use `embeddings_column`.
            try:
                tbl = db.create_table(table_name, df, embeddings_column="embedding")
            except TypeError:
                tbl = db.create_table(table_name, df)
            print(f"Created table: {table_name}")
        except Exception:
            # table may already exist; reopen and append
            try:
                tbl = db.open_table(table_name)
                tbl.add(df)
                print(f"Appended to existing table: {table_name}")
            except Exception as exc:
                print("[warn] LanceDB table access failed:", exc)
                raise

        print(f"Rows stored: {len(df)}")
        return True
    except Exception as exc:
        print("[warn] LanceDB storage failed:", exc)
        print("Falling back to saving embeddings to local NPZ (for FAISS or later use)")
        np.savez_compressed(f"{table_name}_embeddings.npz", embeddings=embeddings, texts=documents, labels=labels)
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=2000, help="Number of rows to index (default 2000)")
    parser.add_argument("--db-path", type=str, default="./rag_lancedb_db", help="LanceDB folder path")
    parser.add_argument("--table", type=str, default="yelp_reviews", help="Table name in LanceDB")
    parser.add_argument("--dataset", type=str, default="fancyzhx/ag_news",
                        help="Dataset ID on Hugging Face (namespaced names are safer across versions)")

    args = parser.parse_args()

    print_section(f"Loading dataset: {args.dataset}")
    split = f"train[:{args.limit}]"
    dataset = load_dataset(args.dataset, split=split)
    print(f"Loaded rows: {len(dataset)}")

    documents = dataset["text"]
    labels = dataset["label"]

    print_section("Generating embeddings (sentence-transformers/all-MiniLM-L6-v2)")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    batch_size = 64
    embeddings = []
    for i in tqdm(range(0, len(documents), batch_size)):
        batch = documents[i : i + batch_size]
        emb = model.encode(batch, convert_to_numpy=True, normalize_embeddings=True)
        embeddings.append(emb)
    embeddings = np.vstack(embeddings)

    print(f"Embeddings shape: {embeddings.shape}")

    ok = build_and_store(args.db_path, args.table, documents, labels, embeddings.tolist())
    if ok:
        print_section("Done: Database prepared")
    else:
        print_section("Done: Embeddings saved to NPZ fallback")


if __name__ == "__main__":
    main()
