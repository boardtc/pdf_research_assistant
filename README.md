# PDF Research Assistant

![Python 3.13.7](https://img.shields.io/badge/python-3.13.7-blue)
![MIT License](https://img.shields.io/badge/license-MIT-green)
![PaperQA2](https://img.shields.io/badge/PaperQA2-FutureHouse-orange)

A local PDF Research Assistant built with [PaperQA2](https://github.com/Future-House/paper-qa), backed by either a manifest-controlled document library or all PDFs under a chosen root folder.

## Getting Started

### Requirements

- Python 3.13.7
- An OpenAI API key

Install the Python dependencies:

```bash
cd ~/gitrepos/pdf_research_assistant
pip install -r requirements.txt
```

Create an OpenAI API key in the OpenAI dashboard:

- [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)

### First-Time Setup

1. Copy `.env.example` to `.env`.
2. Set `OPENAI_API_KEY` in `.env`.
3. Set `PAPER_DIR` in `.env` to the common root folder containing your PDFs.
4. Optional: copy `manifest.example.csv` to `manifest.csv` if you want curated scope and metadata.
5. If you use `manifest.csv`, replace the example rows with paths relative to your chosen `PAPER_DIR`.

## Usage

### Streamlit UI

```bash
cd ~/gitrepos/pdf_research_assistant
streamlit run pdf_research_assistant.py
```

Streamlit will open the app in your browser automatically and will also print the local URL in the terminal. It usually uses `http://localhost:8501` unless that port is already in use.
On first use, there is no search index yet. The first query will build it, and for a large PDF library this can take a significant amount of time.

### CLI

```bash
cd ~/gitrepos/pdf_research_assistant
python query_papers.py
```

Type a question in the UI or CLI to search your indexed PDFs and return a cited answer with page references.

## Configuration

The app and CLI read configuration from environment variables and will also load values from `.env` when present.

By default, `INDEX_DIR` and `MANIFEST_PATH` are resolved relative to the repository root, so the project can be moved without changing code.
`PAPER_DIR` can point to any folder on your system. If `manifest.csv` is present, it stores paths relative to that one common PDF root. If `manifest.csv` is absent, the app will index all PDFs under `PAPER_DIR`.

An OpenAI API key is required for querying and for any indexing steps that need model calls. Set `OPENAI_API_KEY` in `.env` or in your shell environment before running the app.

| Variable | Purpose | Default |
| --- | --- | --- |
| `OPENAI_API_KEY` | OpenAI API key for PaperQA2 queries | unset |
| `PAPER_DIR` | Common root folder containing your PDFs | required |
| `INDEX_DIR` | Local PaperQA index directory | `<repo-root>/index` |
| `MANIFEST_PATH` | Optional CSV manifest of allowed PDFs | `<repo-root>/manifest.csv` |

See `.env.example` for the expected keys. Leave `INDEX_DIR` and `MANIFEST_PATH` unset if you want to use the repo-root defaults.

`bootstrap.py` is internal shared runtime wiring for the UI, CLI, and rebuild script. In normal use, update `.env` rather than editing `bootstrap.py`.

## Notes

- On first use, there is no index yet. The first query builds it.
- For a large PDF library, initial indexing can take a significant amount of time.
- The index is stored in `INDEX_DIR`.
- If `manifest.csv` exists, the app uses it to decide which PDFs are in scope and which metadata to use.
- If `manifest.csv` does not exist, the app indexes all PDFs under `PAPER_DIR`.
- Answers cite specific pages from your PDFs when available.

## Adding New PDFs

1. Add the PDF under your configured `PAPER_DIR`.
2. If you are using a manifest, add a row to `manifest.csv`.
3. Rebuild the index with `python rebuild_index.py` before querying again.
4. Start the UI with `streamlit run pdf_research_assistant.py`, or start the CLI with `python query_papers.py`.
5. Ask a question about your PDFs.
