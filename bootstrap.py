"""Shared startup and runtime wiring for the UI, CLI, and rebuild scripts.

Edit .env or environment variables for local configuration; this module is
internal project wiring.
"""

import csv
import os
import pickle
import zlib
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
from paperqa import Settings
from paperqa.settings import AgentSettings, IndexSettings, ParsingSettings

load_dotenv()

PROXY_ENV_VARS = ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY")
LOOPBACK_PROXY_HOSTS = {"127.0.0.1", "localhost", "::1"}

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_INDEX_DIR = PROJECT_ROOT / "index"
DEFAULT_MANIFEST_PATH = PROJECT_ROOT / "manifest.csv"
FAILED_DOCUMENT_ADD_ID = "ERROR"
MODEL_NAME = "gpt-4o-mini"
PDF_EXTENSIONS = {".pdf"}


def sanitize_proxy_environment() -> None:
    """Drop obviously broken loopback proxy placeholders from the process environment."""
    for name in PROXY_ENV_VARS:
        value = os.getenv(name)
        if not value:
            continue
        parsed = urlparse(value)
        if parsed.hostname in LOOPBACK_PROXY_HOSTS and parsed.port == 9:
            os.environ.pop(name, None)


sanitize_proxy_environment()


def env_path(name: str, default: Path | None = None, required: bool = False) -> Path:
    value = os.getenv(name)
    if value:
        return Path(value).expanduser()
    if default is not None:
        return default
    if required:
        raise RuntimeError(
            f"{name} is not set. Configure it in .env or your environment before running the app."
        )
    raise RuntimeError(f"{name} is not set.")


PAPER_DIR = env_path("PAPER_DIR", required=True)
INDEX_DIR = env_path("INDEX_DIR", DEFAULT_INDEX_DIR)
MANIFEST_PATH = env_path("MANIFEST_PATH", DEFAULT_MANIFEST_PATH)


def manifest_exists(manifest_path: Path = MANIFEST_PATH) -> bool:
    return manifest_path.exists()


def load_allowed_manifest_paths(manifest_path: Path = MANIFEST_PATH) -> set[str]:
    if not manifest_exists(manifest_path):
        return set()
    with open(manifest_path, newline="", encoding="utf-8-sig") as handle:
        return {
            row["file_location"].replace("/", "\\")
            for row in csv.DictReader(handle)
            if row.get("file_location")
        }


ALLOWED_PATHS = load_allowed_manifest_paths()
USE_MANIFEST = bool(ALLOWED_PATHS)


def normalize_file_location(file_location: str | Path, paper_dir: Path = PAPER_DIR) -> str:
    value = str(file_location).replace("/", "\\")
    prefix = str(paper_dir).replace("/", "\\") + "\\"
    if value.startswith(prefix):
        value = value[len(prefix) :]
    return value


def only_manifest(path: str | Path) -> bool:
    if not USE_MANIFEST:
        return Path(path).suffix.lower() in PDF_EXTENSIONS
    rel = str(Path(path).relative_to(PAPER_DIR))
    return rel in ALLOWED_PATHS


def get_indexed_doc_count(index_dir: Path = INDEX_DIR) -> int:
    if not index_dir.exists():
        return 0
    indexed = set()
    for file_index in index_dir.glob("*/files.zip"):
        try:
            data = pickle.loads(zlib.decompress(file_index.read_bytes()))
        except Exception:
            continue
        for file_location, status in data.items():
            if status == FAILED_DOCUMENT_ADD_ID:
                continue
            normalized = normalize_file_location(file_location)
            if not USE_MANIFEST or normalized in ALLOWED_PATHS:
                indexed.add(normalized)
    return len(indexed)


def get_failed_files(index_dir: Path = INDEX_DIR) -> list[str]:
    failed = []
    if not index_dir.exists():
        return failed
    for file_index in index_dir.glob("*/files.zip"):
        try:
            data = pickle.loads(zlib.decompress(file_index.read_bytes()))
        except Exception:
            continue
        for file_location, status in data.items():
            if status == FAILED_DOCUMENT_ADD_ID:
                failed.append(str(file_location))
    return sorted(set(failed))


def build_settings() -> Settings:
    return Settings(
        llm=MODEL_NAME,
        summary_llm=MODEL_NAME,
        llm_config={"rate_limit": {MODEL_NAME: "30000 per 1 minute"}},
        summary_llm_config={"rate_limit": {MODEL_NAME: "30000 per 1 minute"}},
        parsing=ParsingSettings(multimodal=False, use_doc_details=False),
        agent=AgentSettings(
            agent_llm=MODEL_NAME,
            agent_llm_config={"rate_limit": {MODEL_NAME: "30000 per 1 minute"}},
            index=IndexSettings(
                paper_directory=PAPER_DIR,
                index_directory=INDEX_DIR,
                manifest_file=MANIFEST_PATH if manifest_exists() else None,
                use_absolute_paper_directory=False,
                recurse_subdirectories=True,
                concurrency=1,
                files_filter=only_manifest,
            ),
        ),
    )
