import traceback

import streamlit as st
from paperqa import ask

from bootstrap import ALLOWED_PATHS, build_settings, get_failed_files, get_indexed_doc_count


def flatten_exception_messages(exc, depth=0):
    indent = "  " * depth
    lines = [f"{indent}{type(exc).__name__}: {exc}"]
    children = getattr(exc, "exceptions", None)
    if children:
        for child in children:
            lines.extend(flatten_exception_messages(child, depth + 1))
    return lines


@st.cache_resource
def get_settings():
    return build_settings()


st.title("PDF Research Assistant")

manifest_count = len(ALLOWED_PATHS)
indexed_count = get_indexed_doc_count()
failed_files = get_failed_files()

if indexed_count == 0:
    st.warning(
        f"Index not found. The first question will rebuild the index for {manifest_count} manifest PDFs, "
        "which may take a long time."
    )
    st.info("A rebuild starts only after you submit a question below.")
elif indexed_count < manifest_count:
    st.warning(
        f"Index is incomplete: {indexed_count} of {manifest_count} manifest PDFs appear indexed. "
        "The next question should continue or trigger indexing work."
    )
else:
    st.caption(f"Index available for {indexed_count} manifest PDFs.")

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
            st.caption(f"Cost: ${item['cost']:.4f}")

question = st.chat_input("Ask a question about your PDFs...")

if question:
    st.session_state.history.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Searching PDFs..."):
            try:
                response = ask(question, settings=get_settings())
                answer = response.session.formatted_answer
                cost = response.session.cost
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
                st.error(answer)
                st.caption("Cost: $0.0000")
                st.code("".join(traceback.format_exception(exc)))
            else:
                st.markdown(answer)
                st.caption(f"Cost: ${cost:.4f}")

    st.session_state.history.append({"role": "assistant", "content": answer, "cost": cost})
    st.session_state.total_cost += cost
    st.session_state.query_count += 1
    st.rerun()
