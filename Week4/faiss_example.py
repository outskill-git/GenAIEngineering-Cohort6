from datasets import load_dataset
from sentence_transformers import SentenceTransformer
import faiss


def print_section(title: str, width: int = 78) -> None:
    border = "=" * width
    print(f"\n{border}")
    print(f"{title.center(width)}")
    print(border)


def load_ag_news_subset():
    dataset_id_candidates = ["ag_news", "fancyzhx/ag_news"]
    split = "train[:1000]"

    for dataset_id in dataset_id_candidates:
        try:
            print_section(f"Loading dataset: {dataset_id}")
            return load_dataset(dataset_id, split=split), dataset_id
        except Exception as exc:
            print(f"  [warn] {dataset_id} failed: {type(exc).__name__}: {exc}")
            last_error = exc

    raise RuntimeError(
        f"Unable to load AG News dataset with known IDs: {dataset_id_candidates}"
    ) from last_error


def main() -> None:
    dataset, dataset_id = load_ag_news_subset()
    print_section(f"Dataset source: {dataset_id}")
    documents = dataset["text"]
    print(f"Loaded rows: {len(documents)}")

    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    print_section("Generating document embeddings")
    doc_embeddings = model.encode(
        documents,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    print(f"Embedding shape: {doc_embeddings.shape}")

    print_section("Building FAISS index")
    dimension = doc_embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(doc_embeddings)
    print(f"Vector count indexed: {index.ntotal}")

    query = "Microsoft launches a new AI product"
    query_embedding = model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    scores, indices = index.search(query_embedding, k=5)

    print_section("Top-k results")
    print(f"Query: {query}\n")

    for rank, (idx, score) in enumerate(zip(indices[0], scores[0]), start=1):
        print(f"Rank {rank:>2}")
        print(f"Similarity: {score:.4f}")
        print(f"Document id: {idx}")
        print(documents[idx])
        print("-" * 78)


if __name__ == "__main__":
    main()
