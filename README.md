# PDF Research Assistant

![Python 3.13.7](https://img.shields.io/badge/python-3.13.7-blue)
![MIT License](https://img.shields.io/badge/license-MIT-green)
![PaperQA2](https://img.shields.io/badge/PaperQA2-FutureHouse-orange)

A local PDF Research Assistant built with [PaperQA2](https://github.com/Future-House/paper-qa), backed by a manifest-controlled document library.

## Usage

### Streamlit UI

```bash
cd ~/paperqa_matl
streamlit run pdf_research_assistant.py
```

Opens in your browser on the local Streamlit port.

### CLI

```bash
cd ~/paperqa_matl
python query_papers.py
```

Type a question in the UI or CLI to search your indexed PDFs and return a cited answer with page references.

## Configuration

The app and CLI read configuration from environment variables and will also load values from `.env` when present.

By default, `INDEX_DIR` and `MANIFEST_PATH` are resolved relative to the repository root, so the project can be moved without changing code.

| Variable | Purpose | Default |
| --- | --- | --- |
| `OPENAI_API_KEY` | OpenAI API key for PaperQA2 queries | unset |
| `PAPER_DIR` | Root folder containing PDFs | `H:/My Drive/SETU/MATL/Assessment & Feedback` |
| `INDEX_DIR` | Local PaperQA index directory | `<repo-root>/index` |
| `MANIFEST_PATH` | CSV manifest of allowed PDFs | `<repo-root>/manifest.csv` |

See `.env.example` for the expected keys. Leave `INDEX_DIR` and `MANIFEST_PATH` unset if you want to use the repo-root defaults.

`bootstrap.py` is internal shared runtime wiring for the UI, CLI, and rebuild script. In normal use, update `.env` rather than editing `bootstrap.py`.

## Notes

- The first run after adding new papers will rebuild or extend the index.
- The index is stored in `INDEX_DIR`.
- The app uses `manifest.csv` to decide which PDFs are available for search.
- Answers cite specific pages from your PDFs when available.

## Adding New PDFs

1. Add the PDF under your configured `PAPER_DIR`.
2. Add a row to `manifest.csv`.
3. Rebuild the index if needed with `python rebuild_index.py`.
4. Start the UI or CLI and query your PDFs.
