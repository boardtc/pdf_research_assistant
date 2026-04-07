# Testing

This project keeps test tooling separate from runtime dependencies so standard users do not need to install it.

## Install test dependencies

```powershell
python -m pip install -r requirements-dev.txt
```

## Enable the pre-push test hook

This repository includes a versioned Git `pre-push` hook in `.githooks/pre-push` that runs the full test suite before each push.

Run this once in your local clone to tell Git to use the tracked hooks directory:

```powershell
git config core.hooksPath .githooks
```

After that, every `git push` from that clone will run:

```powershell
python -m pytest
```

If the tests fail, Git blocks the push.

Important:

- The hook file is tracked in the repository, but `core.hooksPath` is a local Git setting stored in `.git/config`.
- That means forks and fresh clones do not automatically enable the hook unless the contributor runs `git config core.hooksPath .githooks`.
- To enforce tests for everyone regardless of local hook setup, use CI as well.

## GitHub Actions CI

This repository also runs the test suite in GitHub Actions on every push and pull request.

The workflow lives at `.github/workflows/tests.yml` and currently runs:

```powershell
python -m pytest
```

on a `windows-latest` runner.

This CI workflow complements the local `pre-push` hook:

- the local hook gives fast feedback before a push leaves your machine
- GitHub Actions provides a consistent remote check for pushes and pull requests
- branch protection can require the `test` status check before changes are merged into `master`

## Run all tests

```powershell
python -m pytest
```

## Run one test file

```powershell
python -m pytest tests\test_query_once.py
```

```powershell
python -m pytest tests\test_bootstrap.py
```

```powershell
python -m pytest tests\test_pdf_research_assistant.py
```

```powershell
python -m pytest tests\test_query_papers.py
```

```powershell
python -m pytest tests\test_rebuild_index.py
```

## Run one test with verbose output

```powershell
python -m pytest -v tests\test_query_once.py
```

```powershell
python -m pytest -v tests\test_bootstrap.py
```

```powershell
python -m pytest -v tests\test_pdf_research_assistant.py
```

```powershell
python -m pytest -v tests\test_query_papers.py
```

```powershell
python -m pytest -v tests\test_rebuild_index.py
```

## Run coverage for one file

```powershell
python -m pytest tests\test_query_once.py --cov=query_once --cov-report=term-missing
```

```powershell
python -m pytest tests\test_bootstrap.py --cov=bootstrap --cov-report=term-missing
```

```powershell
python -m pytest tests\test_pdf_research_assistant.py --cov=pdf_research_assistant --cov-report=term-missing
```

```powershell
python -m pytest tests\test_query_papers.py --cov=query_papers --cov-report=term-missing
```

```powershell
python -m pytest tests\test_rebuild_index.py --cov=rebuild_index --cov-report=term-missing
```

## Run coverage for the whole project

```powershell
python -m pytest --cov=. --cov-report=term-missing
```

## Current test strategy

- Unit tests use `pytest` as the test runner.
- Coverage reporting uses `pytest-cov`.
- Mocking uses Python's built-in `unittest.mock`.
- Current unit test files are `tests/test_query_once.py`, `tests/test_bootstrap.py`, `tests/test_pdf_research_assistant.py`, `tests/test_query_papers.py`, and `tests/test_rebuild_index.py`.
- `query_once.py` and `bootstrap.py` have straightforward function-oriented tests.
- `pdf_research_assistant.py` includes heavier mocking because the Streamlit page executes UI logic at import time.

## Where to record results

- Keep test and coverage commands in this file.
- Put actual run results in pull requests, GitHub tickets, or CI logs rather than a checked-in results file.
- Do not maintain a permanent results document in the repo, because it will go stale quickly.
