# PDF Research Assistant

![Python 3.11%2B](https://img.shields.io/badge/python-3.11%2B-blue)
![MIT License](https://img.shields.io/badge/license-MIT-green)
![PaperQA2](https://img.shields.io/badge/PaperQA2-FutureHouse-orange)

A local PDF research assistant built with [PaperQA2](https://github.com/Future-House/paper-qa). It can use either a manifest-controlled document library or all PDFs under a chosen root folder.

Core indexing and querying work on Windows, macOS, and Linux. The Streamlit `Copy answer` clipboard button is currently Windows-only.

![PDF Research Assistant screenshot](images/streamlit_app.jpg)

> **Important**
> PaperQA2 uses retrieval-augmented generation (RAG). It returns real source passages and page references, but it can still overstate, paraphrase, or extrapolate beyond what the source explicitly says. Treat answers as a starting point for exploration, not as a citable summary. Always verify important claims against the source passages and the original PDF.

## Getting Started

### Requirements

- Python 3.11 or newer
- An OpenAI API key

Install the Python dependencies:

```bash
cd ~/gitrepos/pdf-research-assistant
python -m pip install -e .
```

For development tools such as `pytest` and coverage reporting:

```bash
python -m pip install -e .[dev]
```

Create an OpenAI API key in the OpenAI dashboard:

- [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)

### Setup

1. Copy `.env.example` to `.env`.
2. Set `OPENAI_API_KEY` in `.env`.
3. Set `PAPER_DIR` in `.env` to the root folder containing your PDFs.
4. Optional: copy `manifest.example.csv` to `manifest.csv` if you want curated scope and metadata.
5. If you use `manifest.csv`, replace the example rows with paths relative to your chosen `PAPER_DIR`.

## Project Layout

The code now uses a standard `src` layout:

- `src/pdf_research_assistant/` is the Python package directory
- `src/` keeps imports honest during development and testing
- `pyproject.toml` defines dependencies and the `pdf-research` and `pdf-research-rebuild` commands

The extra `pdf_research_assistant` folder under `src` is the actual importable package name, so imports like `from pdf_research_assistant.bootstrap import build_settings` continue to work cleanly.

## Usage

### Streamlit UI

```bash
cd ~/gitrepos/pdf-research-assistant
streamlit run src/pdf_research_assistant/app.py
```

Streamlit usually opens the app in your browser automatically and prints the local URL in the terminal. By default, it uses `http://localhost:8501` unless that port is already in use.

The Streamlit sidebar shows:

- query count for the current session
- total session cost
- a button to clear the chat

Each assistant response also includes:

- a `Copy answer` button that copies the full answer text to the clipboard on Windows
- a `Show source passages` expander with the retrieved evidence passages used for the answer

Clipboard support for the `Copy answer` button is currently implemented for Windows only.

On first use, there is no search index yet. The first query builds it, which can take a while for a large PDF library.

Each question runs in a fresh helper process so repeated questions in the same session start with clean query state.

### CLI

```bash
cd ~/gitrepos/pdf-research-assistant
pdf-research
```

Type a question at the prompt to search your indexed PDFs and return a cited answer with page references. Type `quit` to exit.

Like the Streamlit app, the CLI runs each question in a fresh helper process so repeated questions start with clean query state.

### Rebuild Index

```bash
cd ~/gitrepos/pdf-research-assistant
pdf-research-rebuild
```

Use this when:

- running the project for the first time and you want to build the index explicitly
- you add new PDFs and want to rebuild before querying again
- you want a terminal-only indexing run instead of letting the first query build the index

On a clean rebuild, it is normal to see `Manifest PDFs: <n>` and `Indexed before run: 0` before indexing starts.

See `windows-helper-commands.example.md` for optional PowerShell commands that help check index build progress and troubleshoot rebuild issues on Windows. If you want a version with your own local paths ready to copy and paste, create `windows-helper-commands.md` from it.

## Environment Variables

The app and CLI read settings from environment variables and load values from `.env` when present.

By default, `INDEX_DIR` and `MANIFEST_PATH` are resolved relative to the repository root, so the project can be moved without changing code. `PAPER_DIR` can point to any folder on your system using normal paths for your OS. If `manifest.csv` is present, it stores paths relative to that root folder. If `manifest.csv` is absent, the app indexes all PDFs under `PAPER_DIR`.

| Variable | Purpose | Default |
| --- | --- | --- |
| `OPENAI_API_KEY` | OpenAI API key for PaperQA2 queries | unset |
| `PAPER_DIR` | Common root folder containing your PDFs | required |
| `INDEX_DIR` | Optional override for where the local PaperQA index is stored | `<repo-root>/index` |
| `MANIFEST_PATH` | Optional CSV manifest of allowed PDFs | `<repo-root>/manifest.csv` |
| `PDF_RESEARCH_ASSISTANT_SYNC_DIR` | Optional destination folder for post-push copies of `.env`, `manifest.csv`, and your private `windows-helper-commands.md` notes | unset |

See `.env.example` for the expected keys. Leave `INDEX_DIR` and `MANIFEST_PATH` unset to use the repo-root defaults.

If `PDF_RESEARCH_ASSISTANT_SYNC_DIR` is set, the tracked `post-push` hook copies `.env` and `manifest.csv` when present. It also copies `windows-helper-commands.md` if you created a private local version for your own use.

## Additional Notes

- The search index is stored in the folder set by `INDEX_DIR`.
- If `manifest.csv` exists, the app uses it to decide which PDFs are in scope and which metadata to use.
- If `manifest.csv` does not exist, the app indexes all PDFs under `PAPER_DIR`.
- `windows-helper-commands.example.md` is a safe-to-share template. If you want a version with your own local paths ready to copy and paste, create `windows-helper-commands.md` from it.
- The app automatically ignores the broken loopback proxy placeholder `127.0.0.1:9` if it appears in `HTTP_PROXY`, `HTTPS_PROXY`, or `ALL_PROXY`.
- `src/pdf_research_assistant/query_once.py` is an internal helper used by the app and CLI; it is not intended as a separate user entry point.
- If PaperQA reports that a PDF is empty but the file opens normally, it may be image-only and need OCR before it can be indexed.
- Answers cite specific pages from your PDFs when available.

## Adding New PDFs

1. Add the PDF under your configured `PAPER_DIR`.
2. If you are using a manifest, add a row to `manifest.csv`.
3. Rebuild the index with `pdf-research-rebuild` before querying again.
4. Start the UI or CLI and ask a question about your PDFs.
