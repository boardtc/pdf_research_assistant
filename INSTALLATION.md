# Installation

## Prerequisites

- Python 3.11+
- Git Bash (MINGW64)
- OpenAI API key with billing enabled (platform.openai.com)

## Steps

**1. Create project folder**
```bash
mkdir ~/paperqa_matl
cd ~/paperqa_matl
```

**2. Install dependencies**
```bash
pip install paper-qa streamlit --break-system-packages
```

**3. Set OpenAI API key**
```bash
echo 'export OPENAI_API_KEY="sk-..."' >> ~/.bashrc
source ~/.bashrc
```

**4. Add manifest and scripts**

Place the following files in `~/paperqa_matl/`:
- `manifest.csv` — list of PDFs to index (see format below)
- `app.py` — Streamlit app

**5. Run**
```bash
streamlit run app.py
```

---

## Manifest format

`manifest.csv` controls which PDFs are indexed. Paths are relative to your paper directory.

```
file_location,title,citation,doi
Session 5/Price.pdf,Feedback: all that effort but what is the effect?,"Price et al. (2010)",10.1080/02602930903541007
```

## Paper directory

Default: `H:/My Drive/SETU/MATL/Assessment & Feedback`

To change, edit `PAPER_DIR` in `app.py` and `query_papers.py`.

## Index location

Default: `~/paperqa_matl/index/`

Delete this folder to force a full rebuild after adding new papers.

## Claude Code (SETU network)

The following are already set in `~/.bashrc` but required for Claude Code on the SETU corporate network:
```bash
export CLAUDE_CODE_GIT_BASH_PATH="..."  # path to git.exe
export NODE_TLS_REJECT_UNAUTHORIZED=0
export OPENAI_API_KEY="sk-..."
```

## Adding new PDFs

**1.** Add the PDF to the appropriate folder under `H:/My Drive/SETU/MATL/Assessment & Feedback/`

**2.** Add a row to `~/paperqa_matl/manifest.csv`:
```
Session 8/NewPaper.pdf,Title of Paper,"Author (Year) Journal",10.xxxx/xxxxx
```

**3.** Delete the old index to force a rebuild:
```bash
rm -rf ~/paperqa_matl/index/
```

**4.** Run the app as normal — it will re-index on first launch:
```bash
streamlit run app.py
```

The re-index takes a few minutes depending on how many new PDFs were added.
