import subprocess
import traceback
from pathlib import Path

import streamlit as st
from paperqa.agents.main import agent_query
from paperqa.utils import run_or_ensure

from bootstrap import ALLOWED_PATHS, USE_MANIFEST, build_settings, get_failed_files, get_indexed_doc_count


def flatten_exception_messages(exc, depth=0):
    indent = "  " * depth
    lines = [f"{indent}{type(exc).__name__}: {exc}"]
    children = getattr(exc, "exceptions", None)
    if children:
        for child in children:
            lines.extend(flatten_exception_messages(child, depth + 1))
    return lines


def copy_to_clipboard(text: str) -> None:
    clip_path = Path(r"C:\Windows\System32\clip.exe")
    subprocess.run([str(clip_path)], input=text, text=True, check=True)


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
            text = getattr(ctx, "text", None)
            if text is None:
                continue
            st.subheader(getattr(text, "name", "Source"))
            st.write(getattr(ctx, "context", ""))
            raw_text = getattr(text, "text", "")
            if raw_text:
                st.caption("Raw chunk text")
                st.write(raw_text)


@st.cache_resource
def get_settings():
    return build_settings()


st.title("PDF Research Assistant")

manifest_count = len(ALLOWED_PATHS)
indexed_count = get_indexed_doc_count()
failed_files = get_failed_files()

if indexed_count == 0 and USE_MANIFEST:
    st.warning(
        f"Index not found. The first question will rebuild the index for {manifest_count} manifest PDFs, "
        "which may take a long time."
    )
    st.info("A rebuild starts only after you submit a question below.")
elif USE_MANIFEST and indexed_count < manifest_count:
    st.warning(
        f"Index is incomplete: {indexed_count} of {manifest_count} manifest PDFs appear indexed. "
        "The next question should continue or trigger indexing work."
    )
elif indexed_count == 0:
    st.warning("Index not found. The first question will build the PDF index, which may take a long time.")
    st.info("No manifest.csv was found, so all PDFs under PAPER_DIR are in scope.")
else:
    if USE_MANIFEST:
        st.caption(f"Index available for {indexed_count} manifest PDFs.")
    else:
        st.caption(f"Index available for {indexed_count} PDFs under PAPER_DIR.")

if failed_files:
    st.error(f"{len(failed_files)} PDF(s) failed to index.")
    with st.expander("Show failed PDFs"):
        for file_location in failed_files:
            st.code(file_location)

if "history" not in st.session_state:
    st.session_state.history = []
if "total_cost" not in st.session_state:
    st.session_state.total_cost = 0.0
if "query_count" not in st.session_state:
    st.session_state.query_count = 0

with st.sidebar:
    st.header("Usage")
    st.metric("Queries this session", st.session_state.query_count)
    st.metric("Total cost this session", f"${st.session_state.total_cost:.4f}")
    if st.button("Clear chat"):
        st.session_state.history = []
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
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Searching PDFs..."):
            try:
                settings = get_settings()
                response = run_or_ensure(
                    coro=agent_query(
                        question,
                        settings,
                        agent_type=settings.agent.agent_type,
                    )
                )
                answer = response.session.formatted_answer
                cost = response.session.cost
                contexts = list(getattr(response.session, "contexts", []) or [])
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
    st.rerun()
