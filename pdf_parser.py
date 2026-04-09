"""PDF parser helpers with a targeted fallback for known pypdf font-encoding failures."""

from __future__ import annotations

import importlib
from pathlib import Path


def should_fallback_pdf_parse(error: BaseException) -> bool:
    """Return whether a parser error matches the known SymbolSetEncoding failure."""
    return (
        isinstance(error, LookupError)
        and "/SymbolSetEncoding" in str(error)
        or isinstance(error, ValueError)
        and "Crop exceeds page dimensions" in str(error)
    )


def resolve_pdfplumber_page_indexes(
    page_range: int | tuple[int, int] | None, total_pages: int
) -> list[int]:
    """Convert PaperQA-style page ranges into zero-based pdfplumber page indexes."""
    if page_range is None:
        return list(range(total_pages))
    if isinstance(page_range, int):
        return [page_range - 1]
    start_page, end_page = page_range
    return list(range(start_page - 1, end_page))


def parse_pdf_with_pdfplumber(
    path: str | Path,
    page_size_limit: int | None = None,
    page_range: int | tuple[int, int] | None = None,
    **_: object,
) -> object:
    """Parse PDF page text with pdfplumber as a fallback when pypdf cannot decode fonts."""
    try:
        pdfplumber = importlib.import_module("pdfplumber")
    except ImportError as exc:
        raise ImportError(
            "pdfplumber is required for the fallback PDF parser. Install it with `pip install pdfplumber`."
        ) from exc
    paperqa_types = importlib.import_module("paperqa.types")

    parsed_pages: dict[str, str] = {}
    with pdfplumber.open(str(path)) as pdf:
        for page_index in resolve_pdfplumber_page_indexes(page_range, len(pdf.pages)):
            text = pdf.pages[page_index].extract_text() or ""
            if page_size_limit and len(text) > page_size_limit:
                raise ValueError(
                    f"The text in page {page_index} of {len(pdf.pages)} was {len(text)} chars"
                    f" long, which exceeds the {page_size_limit} char limit for the PDF"
                    f" at path {path!r}."
                )
            parsed_pages[str(page_index + 1)] = text
    return paperqa_types.ParsedText(
        content=parsed_pages,
        metadata=paperqa_types.ParsedMetadata(
            parsing_libraries=["pdfplumber"],
            total_parsed_text_length=sum(len(text) for text in parsed_pages.values()),
            count_parsed_media=0,
        ),
    )


def parse_pdf_with_fallback(path: str | Path, **kwargs: object) -> dict[str, str]:
    """Parse PDFs with PaperQA's default pypdf parser, falling back for SymbolSetEncoding errors."""
    paperqa_pypdf = importlib.import_module("paperqa_pypdf")
    try:
        return paperqa_pypdf.parse_pdf_to_pages(path, **kwargs)
    except Exception as exc:
        if not should_fallback_pdf_parse(exc):
            raise
        if isinstance(exc, ValueError) and "Crop exceeds page dimensions" in str(exc):
            safe_kwargs = dict(kwargs)
            safe_kwargs["parse_media"] = False
            return parse_pdf_with_pdfplumber(path, **safe_kwargs)
    return parse_pdf_with_pdfplumber(path, **kwargs)
