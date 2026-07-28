"""Standalone Hugging Face hybrid RAG chatbot demo.

Run:
    python3 rag_chatbot.py

This example intentionally does not import anything from the Day 1 code. It uses
LangChain libraries for chunking, retrieval, and fusion.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import os
import re
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

warnings.filterwarnings(
    "ignore",
    message=r"`langchain-community` is being sunset.*",
    category=DeprecationWarning,
)

from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from transformers.utils import logging as transformers_logging

try:
    from huggingface_hub.utils import logging as hub_logging
except ImportError:
    hub_logging = None

try:
    from langchain_classic.retrievers import EnsembleRetriever
except ImportError:  # Older LangChain versions exposed it from langchain.retrievers.
    from langchain.retrievers import EnsembleRetriever

from langchain_community.retrievers import BM25Retriever


ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "company_ai_handbook.md"
DEFAULT_EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
DEFAULT_GENERATOR_MODEL = os.getenv("GENERATOR_MODEL", "google/flan-t5-small")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
transformers_logging.set_verbosity_error()
if hub_logging:
    hub_logging.set_verbosity_error()


@contextlib.contextmanager
def quiet_model_loading():
    """Hide noisy model-loading progress bars while keeping real Python exceptions."""
    with contextlib.redirect_stderr(io.StringIO()):
        yield


PROMPT = PromptTemplate.from_template(
    """You are a careful internal support assistant.
Answer using only the retrieved context and conversation history.
If the answer is not in the context, say you do not know rather than hallucinating a made up answer.
Keep the answer concise.

Retrieved context:
{retrieved_context}

Conversation history:
{chat_history}

Current question:
{question}

Answer:"""
)


@dataclass
class ChatTurn:
    question: str
    answer: str


class LocalSeq2SeqGenerator:
    """Small wrapper around a local Hugging Face seq2seq model that acts as the final generator."""

    def __init__(self, model_name: str, max_input_tokens: int = 1024, max_new_tokens: int = 160):
        self.model_name = model_name
        self.max_input_tokens = max_input_tokens
        self.max_new_tokens = max_new_tokens
        with quiet_model_loading():
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

    def generate(self, prompt: str) -> str:
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=self.max_input_tokens,
        )
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=self.max_new_tokens,
            do_sample=False,
            num_beams=2,
        )
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True).strip()


def print_section(title: str) -> None:
    line = "=" * 90
    print(f"\n{line}")
    print(title.upper().center(90))
    print(line)


def print_step(title: str) -> None:
    print(f"\n-- {title}")
    print("-" * min(90, len(title) + 3))


def compact(text: str, limit: int = 360) -> str:
    clean = " ".join(text.split())
    return clean if len(clean) <= limit else clean[:limit].rstrip() + "..."


def tokenize_for_bm25(text: str) -> List[str]:
    """Tokenize for BM25 while preserving ID-like strings with hyphens."""
    return re.findall(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*", text.lower())


def load_markdown(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def chunk_markdown(markdown: str, source_name: str) -> List[Document]:
    """Use LangChain splitters, not custom chunking code."""
    headers_to_split_on = [
        ("#", "document_title"),
        ("##", "section"),
    ]

    # doc aware chunking
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False,
    )
    section_docs = markdown_splitter.split_text(markdown)

    recursive_splitter = RecursiveCharacterTextSplitter(
        chunk_size=650,
        chunk_overlap=120,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = recursive_splitter.split_documents(section_docs)

    for index, doc in enumerate(chunks):
        doc.metadata["chunk_id"] = f"chunk-{index:03d}"
        doc.metadata["source"] = source_name
    return chunks


def build_hybrid_retriever(
    chunks: List[Document],
    embedding_model: str,
    top_k: int,
):
    print_step("Build semantic retriever with Hugging Face embeddings")
    with quiet_model_loading():
        embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            encode_kwargs={"normalize_embeddings": True},
        )
    vector_store = InMemoryVectorStore(embedding=embeddings)
    vector_store.add_documents(chunks)
    semantic_retriever = vector_store.as_retriever(search_kwargs={"k": top_k})
    print(f"Embedding model: {embedding_model}")
    print(f"Semantic retriever top_k: {top_k}")

    print_step("Build BM25 keyword retriever")
    bm25_retriever = BM25Retriever.from_documents(
        chunks,
        preprocess_func=tokenize_for_bm25,
    )
    bm25_retriever.k = top_k
    print("BM25 tokenizer preserves hyphenated IDs such as SKU-AXP-3918.")
    print(f"BM25 retriever top_k: {top_k}")

    print_step("Fuse semantic + BM25 retrieval with LangChain EnsembleRetriever")

    # RRF fusion
    hybrid_retriever = EnsembleRetriever(
        retrievers=[semantic_retriever, bm25_retriever],
        weights=[0.55, 0.45],
        c=60,
    )
    print("Fusion: RRF combines the semantic and BM25 ranked lists.")
    return hybrid_retriever


def build_generator(generator_model: str) -> LocalSeq2SeqGenerator:
    print_step("Load lightweight Hugging Face generator")
    generator = LocalSeq2SeqGenerator(generator_model)
    print(f"Generator model: {generator_model}")
    return generator


def format_docs(docs: Iterable[Document]) -> str:
    blocks = []
    for index, doc in enumerate(docs, start=1):
        chunk_id = doc.metadata.get("chunk_id", "unknown")
        section = doc.metadata.get("section", "unknown section")
        source = doc.metadata.get("source", "unknown source")
        blocks.append(
            f"[Context {index}] source={source} chunk_id={chunk_id} section={section}\n"
            f"{doc.page_content}"
        )
    return "\n\n".join(blocks)


def format_history(history: List[ChatTurn]) -> str:
    if not history:
        return "No previous conversation."
    return "\n\n".join(
        f"Previous question {index}: {turn.question}\nPrevious answer {index}: {turn.answer}"
        for index, turn in enumerate(history, start=1)
    )


def build_prompt_payload(question: str, retrieved_context: str, chat_history: str) -> dict:
    return {
        "question": question,
        "retrieved_context": retrieved_context,
        "chat_history": chat_history,
    }


def answer_question(
    question: str,
    history: List[ChatTurn],
    retriever,
    llm: LocalSeq2SeqGenerator, # generator model
    show_full_prompt: bool,
) -> ChatTurn:
    print_section(f"User question: {question}")

    print_step("Retrieve hybrid context")
    docs = retriever.invoke(question)
    for index, doc in enumerate(docs, start=1):
        print(
            f"{index}. {doc.metadata.get('chunk_id')} | "
            f"section={doc.metadata.get('section', 'unknown')}"
        )
        print(f"   {compact(doc.page_content, 220)}")

    retrieved_context = format_docs(docs)
    chat_history = format_history(history)

    print_step("Conversation history appended to the prompt context")
    print(chat_history)

    payload = build_prompt_payload(
        question=question,
        retrieved_context=retrieved_context,
        chat_history=chat_history,
    )

    prompt_text = PROMPT.format(**payload)
    if show_full_prompt:
        print_step("Full prompt sent to the generator")
        print(prompt_text)
    else:
        print_step("Prompt preview")
        print(compact(prompt_text, 900))

    print_step("Generate answer")
    answer = llm.generate(prompt_text)
    print(answer)
    return ChatTurn(question=question, answer=answer)


def run_demo(args: argparse.Namespace) -> None:
    print_section("Load and chunk document")
    markdown = load_markdown(args.data_path)
    chunks = chunk_markdown(markdown, source_name=args.data_path.name)
    print(f"Data file: {args.data_path}")
    print(f"Raw characters: {len(markdown)}")
    print(f"Chunks created by LangChain splitters: {len(chunks)}")
    for doc in chunks[:3]:
        print(f"- {doc.metadata.get('chunk_id')} | section={doc.metadata.get('section')}")
        print(f"  {compact(doc.page_content, 180)}")

    retriever = build_hybrid_retriever(
        chunks=chunks,
        embedding_model=args.embedding_model,
        top_k=args.top_k,
    )
    llm = build_generator(args.generator_model)

    history: List[ChatTurn] = []

    if args.interactive:
        print_section("Interactive chat")
        print("Type 'exit' to stop.")
        while True:
            question = input("\nQuestion: ").strip()
            if question.lower() in {"exit", "quit", "q"}:
                break
            if not question:
                continue
            turn = answer_question(question, history, retriever, llm, args.show_full_prompt)
            history.append(turn)
        return

    for question in args.question:
        turn = answer_question(question, history, retriever, llm, args.show_full_prompt)
        history.append(turn)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Standalone hybrid RAG chatbot demo.")
    parser.add_argument("--data-path", type=Path, default=DATA_PATH)
    parser.add_argument("--embedding-model", default=DEFAULT_EMBEDDING_MODEL)
    parser.add_argument("--generator-model", default=DEFAULT_GENERATOR_MODEL)
    parser.add_argument("--top-k", type=int, default=4)
    parser.add_argument("--show-full-prompt", action="store_true")
    parser.add_argument("--interactive", action="store_true")
    parser.add_argument(
        "--question",
        action="append",
        default=None,
        help="Question to ask. Pass multiple times for a scripted multi-turn demo.",
    )
    args = parser.parse_args()
    if args.question is None:
        args.question = [
            "When should a logistics escalation be opened for a late order?",
            "What credit can the agent offer in that situation for loyalty plus members?",
        ]
    return args


if __name__ == "__main__":
    run_demo(parse_args())
