"""
OpenAI File Search RAG (Responses API)
Usage:
  python rag.py upload <file_or_dir> [<file_or_dir> ...]
  python rag.py query "<question>"
  python rag.py status
  python rag.py reset
"""

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

STATE_FILE = Path(__file__).parent / ".rag_state.json"
SUPPORTED_EXTENSIONS = {".md", ".pdf"}


def get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set. Copy .env.example to .env and fill it in.")
        sys.exit(1)
    return OpenAI(api_key=api_key)


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2))


# ── upload ────────────────────────────────────────────────────────────────────

def collect_files(paths: list[str]) -> list[Path]:
    collected = []
    for raw in paths:
        p = Path(raw).expanduser().resolve()
        if p.is_dir():
            for ext in SUPPORTED_EXTENSIONS:
                collected.extend(p.rglob(f"*{ext}"))
        elif p.suffix in SUPPORTED_EXTENSIONS:
            collected.append(p)
        else:
            print(f"Skipping {p} (unsupported format, use .md or .pdf)")
    return collected


def cmd_upload(args):
    client = get_client()
    state = load_state()

    if "vector_store_id" not in state:
        vs = client.vector_stores.create(name="rag-store")
        state["vector_store_id"] = vs.id
        save_state(state)
        print(f"Created vector store: {vs.id}")
    else:
        print(f"Using existing vector store: {state['vector_store_id']}")

    vs_id = state["vector_store_id"]

    file_paths = collect_files(args.paths)
    if not file_paths:
        print("No .md or .pdf files found in the given paths.")
        return

    print(f"Uploading {len(file_paths)} file(s)...")
    for p in file_paths:
        print(f"  {p}")

    file_streams = [open(p, "rb") for p in file_paths]
    try:
        batch = client.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vs_id,
            files=file_streams,
        )
    finally:
        for f in file_streams:
            f.close()

    print(f"\nStatus : {batch.status}")
    print(f"Files  : completed={batch.file_counts.completed}  "
          f"failed={batch.file_counts.failed}  "
          f"total={batch.file_counts.total}")

    if batch.status == "completed" or batch.file_counts.completed == batch.file_counts.total:
        print("Vector store ready. You can now run `query`.")


# ── query ─────────────────────────────────────────────────────────────────────

def cmd_query(args):
    client = get_client()
    state = load_state()

    if "vector_store_id" not in state:
        print("No vector store found. Run `upload` first.")
        return

    vs_id = state["vector_store_id"]
    question = args.question
    print(f"Question: {question}\n")

    response = client.responses.create(
        model="gpt-4o-mini",
        input=question,
        instructions=(
            "You are a helpful assistant. "
            "Answer questions strictly based on the provided documents. "
            "If the answer is not in the documents, say so."
        ),
        tools=[{
            "type": "file_search",
            "vector_store_ids": [vs_id],
        }],
    )

    # Extract text and citations from output
    answer_text = ""
    citations: dict[str, str] = {}

    for item in response.output:
        if item.type == "message":
            for block in item.content:
                if block.type == "output_text":
                    text = block.text
                    for ann in getattr(block, "annotations", []):
                        if ann.type == "file_citation":
                            try:
                                file_info = client.files.retrieve(ann.file_id)
                                citations[ann.index] = file_info.filename
                            except Exception:
                                citations[ann.index] = ann.file_id
                    answer_text = text

    print("Answer:")
    print(answer_text.strip())

    if citations:
        print("\nSources:")
        seen = set()
        for name in citations.values():
            if name not in seen:
                print(f"  • {name}")
                seen.add(name)


# ── status ────────────────────────────────────────────────────────────────────

def cmd_status(args):
    client = get_client()
    state = load_state()

    if not state:
        print("No state found. Run `upload` first.")
        return

    vs_id = state.get("vector_store_id")

    if vs_id:
        vs = client.vector_stores.retrieve(vs_id)
        print(f"Vector store  : {vs_id}")
        print(f"  name        : {vs.name}")
        print(f"  status      : {vs.status}")
        print(f"  file count  : {vs.file_counts.completed} completed / "
              f"{vs.file_counts.total} total")
        print(f"  usage bytes : {vs.usage_bytes:,}")


# ── reset ─────────────────────────────────────────────────────────────────────

def cmd_reset(args):
    client = get_client()
    state = load_state()

    confirm = input("This will delete the vector store. Continue? [y/N] ")
    if confirm.lower() != "y":
        print("Aborted.")
        return

    if "vector_store_id" in state:
        try:
            client.vector_stores.delete(state["vector_store_id"])
            print(f"Deleted vector store: {state['vector_store_id']}")
        except Exception as e:
            print(f"Could not delete vector store: {e}")

    STATE_FILE.unlink(missing_ok=True)
    print("State cleared. Run `upload` to start fresh.")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="OpenAI File Search RAG")
    sub = parser.add_subparsers(dest="command", required=True)

    p_upload = sub.add_parser("upload", help="Upload .md / .pdf files to the vector store")
    p_upload.add_argument("paths", nargs="+", help="Files or directories to upload")

    p_query = sub.add_parser("query", help="Ask a question")
    p_query.add_argument("question", help="Your question (wrap in quotes)")

    sub.add_parser("status", help="Show vector store info")
    sub.add_parser("reset", help="Delete vector store and clear state")

    args = parser.parse_args()
    dispatch = {
        "upload": cmd_upload,
        "query": cmd_query,
        "status": cmd_status,
        "reset": cmd_reset,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
