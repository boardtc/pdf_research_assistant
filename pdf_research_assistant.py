import json
import os
import subprocess
import sys
import traceback
from copy import deepcopy
from pathlib import Path

import streamlit as st

os.environ.setdefault("PQA_INDEX_DONT_CACHE_INDEXES", "true")

from bootstrap import get_allowed_paths, get_failed_files, get_indexed_doc_count


def flatten_exception_messages(exc, depth=0):
    indent = "  " * depth
    lines = [f"{indent}{type(exc).__name__}: {exc}"]
    children = getattr(exc, "exceptions", None)
    if children:
        for child in children:
            lines.extend(flatten_exception_messages(child, depth + 1))
    return lines


def copy_to_clipboard(text: str) -> None:
    subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "Set-Clipboard -Value ([Console]::In.ReadToEnd())",
        ],
        input=text,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )


def render_copy_button(text: str, key: str) -> None:
    if st.button("Copy answer", key=key):
        try:
            copy_to_clipboard(text)
        except Exception as exc:
            st.error(f"Copy failed: {exc}")
        else:
            st.toast("Answer copied")


def render_source_passages(contexts):
    if not contexts:
        return
    with st.expander("Show source passages"):
        for ctx in contexts:
            st.subheader(ctx.get("name", "Source"))
            st.write(ctx.get("context", ""))
            raw_text = ctx.get("raw_text", "")
            if raw_text:
                st.caption("Raw chunk text")
                st.write(raw_text)


def run_query_subprocess(question: str) -> tuple[str, float, list[dict]]:
    helper = Path(__file__).with_name("query_once.py")
    result = subprocess.run(
        [sys.executable, str(helper), question],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0 and not result.stdout.strip():
        raise RuntimeError(result.stderr.strip() or "Query subprocess failed.")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "Invalid query response.") from exc
    if not payload.get("ok"):
        raise RuntimeError(f"{payload.get('error_type', 'Error')}: {payload.get('error', 'Unknown error')}")
    return payload["answer"], payload["cost"], payload.get("contexts", [])


@st.cache_resource
def get_persistent_app_state() -> dict:
    return {
        "history": [],
        "total_cost": 0.0,
        "query_count": 0,
    }


def sync_persistent_state(app_state: dict) -> None:
    app_state["history"] = deepcopy(st.session_state.history)
    app_state["total_cost"] = st.session_state.total_cost
    app_state["query_count"] = st.session_state.query_count


st.title("PDF Research Assistant")

allowed_paths = get_allowed_paths()
use_manifest_scope = bool(allowed_paths)
manifest_count = len(allowed_paths)
indexed_count = get_indexed_doc_count()
failed_files = get_failed_files()

if indexed_count == 0 and use_manifest_scope:
    st.warning(
        f"Index not found. The first question will rebuild the index for {manifest_count} manifest PDFs, "
        "which may take a long time."
    )
    st.info("A rebuild starts only after you submit a question below.")
elif use_manifest_scope and indexed_count < manifest_count:
    st.warning(
        f"Index is incomplete: {indexed_count} of {manifest_count} manifest PDFs appear indexed. "
        "The next question should continue or trigger indexing work."
    )
elif indexed_count == 0:
    st.warning("Index not found. The first question will build the PDF index, which may take a long time.")
    st.info("No manifest.csv was found, so all PDFs under PAPER_DIR are in scope.")
else:
    if use_manifest_scope:
        st.caption(f"Index available for {indexed_count} manifest PDFs.")
    else:
        st.caption(f"Index available for {indexed_count} PDFs under PAPER_DIR.")

if failed_files:
    st.error(f"{len(failed_files)} PDF(s) failed to index.")
    with st.expander("Show failed PDFs"):
        for file_location in failed_files:
            st.code(file_location)

app_state = get_persistent_app_state()
if "history" not in st.session_state:
    st.session_state.history = deepcopy(app_state["history"])
if "total_cost" not in st.session_state:
    st.session_state.total_cost = app_state["total_cost"]
if "query_count" not in st.session_state:
    st.session_state.query_count = app_state["query_count"]

with st.sidebar:
    st.header("Usage")
    st.metric("Queries this session", st.session_state.query_count)
    st.metric("Total cost this session", f"${st.session_state.total_cost:.4f}")
    if st.button("Clear chat"):
        st.session_state.history = []
        st.session_state.total_cost = 0.0
        st.session_state.query_count = 0
        sync_persistent_state(app_state)
        st.rerun()

for item in st.session_state.history:
    with st.chat_message(item["role"]):
        st.markdown(item["content"])
        if item["role"] == "assistant" and "cost" in item:
            render_copy_button(item["content"], key=f"copy_history_{item.get('id', 0)}")
            render_source_passages(item.get("contexts", []))
            st.caption(f"Cost: ${item['cost']:.4f}")

question = st.chat_input("Ask a question about your PDFs...")

if question:
    st.session_state.history.append({"role": "user", "content": question})
    sync_persistent_state(app_state)
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Searching PDFs..."):
            try:
                answer, cost, contexts = run_query_subprocess(question)
            except Exception as exc:
                answer = (
                    "Indexing/search failed.\n\n"
                    "Top-level error:\n"
                    f"```\n{type(exc).__name__}: {exc}\n```\n\n"
                    "Underlying error(s):\n"
                    f"```\n{chr(10).join(flatten_exception_messages(exc))}\n```\n\n"
                    "This usually means one document or a parsing/indexing step failed."
                )
                cost = 0.0
                contexts = []
                st.error(answer)
                st.caption("Cost: $0.0000")
                st.code("".join(traceback.format_exception(exc)))
            else:
                st.markdown(answer)
                render_copy_button(answer, key=f"copy_current_{len(st.session_state.history)}")
                render_source_passages(contexts)
                st.caption(f"Cost: ${cost:.4f}")

    st.session_state.history.append(
        {
            "role": "assistant",
            "id": len(st.session_state.history),
            "content": answer,
            "cost": cost,
            "contexts": contexts,
        }
    )
    st.session_state.total_cost += cost
    st.session_state.query_count += 1
    sync_persistent_state(app_state)
    st.rerun()
