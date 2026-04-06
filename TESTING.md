# Testing

This project keeps test tooling separate from runtime dependencies so standard users do not need to install it.

## Install test dependencies

```powershell
python -m pip install -r requirements-dev.txt
```

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

## Run coverage for the whole project

```powershell
python -m pytest --cov=. --cov-report=term-missing
```

## Current test strategy

- Unit tests use `pytest` as the test runner.
- Coverage reporting uses `pytest-cov`.
- Mocking uses Python's built-in `unittest.mock`.
- Current unit test files are `tests/test_query_once.py`, `tests/test_bootstrap.py`, and `tests/test_pdf_research_assistant.py`.
- `query_once.py` and `bootstrap.py` have straightforward function-oriented tests.
- `pdf_research_assistant.py` includes heavier mocking because the Streamlit page executes UI logic at import time.

## Where to record results

- Keep test and coverage commands in this file.
- Put actual run results in pull requests, GitHub tickets, or CI logs rather than a checked-in results file.
- Do not maintain a permanent results document in the repo, because it will go stale quickly.
