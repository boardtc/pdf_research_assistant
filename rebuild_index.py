import asyncio

from paperqa.agents.search import get_directory_index
from bootstrap import ALLOWED_PATHS, USE_MANIFEST, build_settings, get_failed_files, get_indexed_doc_count

settings = build_settings()


def summarize_exception_messages(error: BaseException) -> list[str]:
    """Flatten nested exception groups into a stable list of leaf messages."""
    if isinstance(error, BaseExceptionGroup):
        messages = []
        for child in error.exceptions:
            messages.extend(summarize_exception_messages(child))
        return messages
    return [str(error)]


async def main():
    """Rebuild the PaperQA directory index and print a short before/after status summary."""
    if USE_MANIFEST:
        print(f"Manifest PDFs: {len(ALLOWED_PATHS)}")
    else:
        print("Manifest PDFs: manifest.csv not found; indexing all PDFs under PAPER_DIR")
    print(f"Indexed before run: {get_indexed_doc_count()}")
    rebuild_error = None
    try:
        await get_directory_index(settings=settings, build=True)
    except* Exception as exc_group:
        rebuild_error = exc_group
    failed_files = get_failed_files()
    if rebuild_error and failed_files:
        print("Rebuild completed with parser/indexing errors; recorded failed PDFs will be reported below.")
    elif rebuild_error:
        print("Rebuild completed with parser/indexing errors before any failed PDFs were recorded.")
        for message in summarize_exception_messages(rebuild_error):
            print(f"ERROR: {message}")
    print(f"Indexed after run: {get_indexed_doc_count()}")
    print(f"Failed PDFs: {len(failed_files)}")
    for file_location in failed_files:
        print(f"FAILED: {file_location}")


if __name__ == "__main__":
    asyncio.run(main())
