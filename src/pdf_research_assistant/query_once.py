"""Internal one-shot query helper.

Runs a single PaperQA query in a fresh process so the Streamlit app and CLI
can avoid cross-query asyncio/LiteLLM state issues.
"""

import json
import os
import sys

os.environ.setdefault("PQA_INDEX_DONT_CACHE_INDEXES", "true")

from paperqa import Docs
from paperqa.agents.main import run_agent
from paperqa.utils import run_or_ensure

from pdf_research_assistant.bootstrap import build_settings


def serialize_contexts(contexts):
    """Convert PaperQA context objects into JSON-safe dictionaries for the UI."""
    items = []
    for ctx in list(contexts or []):
        text = getattr(ctx, "text", None)
        items.append(
            {
                "name": getattr(text, "name", "Source") if text else "Source",
                "context": getattr(ctx, "context", "") or "",
                "raw_text": getattr(text, "text", "") if text else "",
            }
        )
    return items


def run_query_payload(question: str) -> dict:
    """Run one PaperQA query and return a serializable success or error payload."""
    try:
        settings = build_settings()
        response = run_or_ensure(
            coro=run_agent(
                Docs(),
                question,
                settings,
                agent_type=settings.agent.agent_type,
            )
        )
        return {
            "ok": True,
            "answer": response.session.formatted_answer,
            "cost": response.session.cost,
            "contexts": serialize_contexts(getattr(response.session, "contexts", [])),
        }
    except Exception as exc:
        return {
            "ok": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }


def main() -> int:
    """Execute the one-shot query CLI contract expected by the app and shell wrapper."""
    if len(sys.argv) != 2:
        print(json.dumps({"ok": False, "error": "Expected exactly one question argument."}))
        return 1

    question = sys.argv[1]
    payload = run_query_payload(question)
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

