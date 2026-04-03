import asyncio

from paperqa.agents.search import get_directory_index
from bootstrap import ALLOWED_PATHS, build_settings, get_failed_files, get_indexed_doc_count

settings = build_settings()


async def main():
    print(f"Manifest PDFs: {len(ALLOWED_PATHS)}")
    print(f"Indexed before run: {get_indexed_doc_count()}")
    await get_directory_index(settings=settings, build=True)
    print(f"Indexed after run: {get_indexed_doc_count()}")
    failed_files = get_failed_files()
    print(f"Failed PDFs: {len(failed_files)}")
    for file_location in failed_files:
        print(f"FAILED: {file_location}")


if __name__ == "__main__":
    asyncio.run(main())
