import asyncio
import importlib
import sys
from pathlib import Path
from types import ModuleType
from unittest import mock

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def rebuild_index_module():
    bootstrap_module = ModuleType("bootstrap")
    search_module = ModuleType("paperqa.agents.search")

    bootstrap_module.ALLOWED_PATHS = {"paper_a.pdf", "paper_b.pdf"}
    bootstrap_module.USE_MANIFEST = True
    bootstrap_module.build_settings = mock.Mock(return_value="settings-object")
    bootstrap_module.get_failed_files = mock.Mock(return_value=[])
    bootstrap_module.get_indexed_doc_count = mock.Mock(side_effect=[1, 2])

    search_module.get_directory_index = mock.AsyncMock(name="get_directory_index")

    with mock.patch.dict(
        sys.modules,
        {
            "bootstrap": bootstrap_module,
            "paperqa.agents.search": search_module,
        },
    ):
        sys.modules.pop("rebuild_index", None)
        module = importlib.import_module("rebuild_index")
        yield module
        sys.modules.pop("rebuild_index", None)


def test_main_prints_manifest_summary_and_rebuild_counts_when_manifest_is_enabled(rebuild_index_module):
    rebuild_index_module.USE_MANIFEST = True
    rebuild_index_module.ALLOWED_PATHS = {"paper_a.pdf", "paper_b.pdf"}
    rebuild_index_module.get_indexed_doc_count = mock.Mock(side_effect=[1, 2])
    rebuild_index_module.get_failed_files = mock.Mock(return_value=[])

    # Mock print so the test can assert on the CLI status output.
    with mock.patch("builtins.print") as print_mock:
        asyncio.run(rebuild_index_module.main())

    rebuild_index_module.get_directory_index.assert_awaited_once_with(
        settings=rebuild_index_module.settings,
        build=True,
    )
    assert print_mock.call_args_list == [
        mock.call("Manifest PDFs: 2"),
        mock.call("Indexed before run: 1"),
        mock.call("Indexed after run: 2"),
        mock.call("Failed PDFs: 0"),
    ]


def test_main_prints_non_manifest_summary_when_manifest_file_is_missing(rebuild_index_module):
    rebuild_index_module.USE_MANIFEST = False
    rebuild_index_module.get_indexed_doc_count = mock.Mock(side_effect=[0, 3])
    rebuild_index_module.get_failed_files = mock.Mock(return_value=[])

    # Mock print so the test can assert on the non-manifest branch output.
    with mock.patch("builtins.print") as print_mock:
        asyncio.run(rebuild_index_module.main())

    assert print_mock.call_args_list == [
        mock.call("Manifest PDFs: manifest.csv not found; indexing all PDFs under PAPER_DIR"),
        mock.call("Indexed before run: 0"),
        mock.call("Indexed after run: 3"),
        mock.call("Failed PDFs: 0"),
    ]


def test_main_prints_each_failed_file_after_rebuild(rebuild_index_module):
    rebuild_index_module.USE_MANIFEST = True
    rebuild_index_module.ALLOWED_PATHS = {"paper_a.pdf"}
    rebuild_index_module.get_indexed_doc_count = mock.Mock(side_effect=[1, 1])
    rebuild_index_module.get_failed_files = mock.Mock(return_value=["bad_a.pdf", "bad_b.pdf"])

    # Mock print so the test can assert that each failed file is reported individually.
    with mock.patch("builtins.print") as print_mock:
        asyncio.run(rebuild_index_module.main())

    assert print_mock.call_args_list == [
        mock.call("Manifest PDFs: 1"),
        mock.call("Indexed before run: 1"),
        mock.call("Indexed after run: 1"),
        mock.call("Failed PDFs: 2"),
        mock.call("FAILED: bad_a.pdf"),
        mock.call("FAILED: bad_b.pdf"),
    ]


def test_main_continues_when_directory_rebuild_raises_exception_group_and_reports_recorded_failed_files(
    rebuild_index_module,
):
    rebuild_index_module.USE_MANIFEST = True
    rebuild_index_module.ALLOWED_PATHS = {"paper_a.pdf"}
    rebuild_index_module.get_indexed_doc_count = mock.Mock(side_effect=[105, 105])
    rebuild_index_module.get_failed_files = mock.Mock(
        return_value=["Session 7/Sadler 2013 Opening-up-feedback-Teaching-learners-to-see Chapter.pdf"]
    )
    rebuild_index_module.get_directory_index = mock.AsyncMock(
        side_effect=ExceptionGroup("unhandled errors in a TaskGroup", [LookupError("unknown encoding: /SymbolSetEncoding")])
    )

    with mock.patch("builtins.print") as print_mock:
        asyncio.run(rebuild_index_module.main())

    assert print_mock.call_args_list == [
        mock.call("Manifest PDFs: 1"),
        mock.call("Indexed before run: 105"),
        mock.call("Rebuild completed with parser/indexing errors; recorded failed PDFs will be reported below."),
        mock.call("Indexed after run: 105"),
        mock.call("Failed PDFs: 1"),
        mock.call("FAILED: Session 7/Sadler 2013 Opening-up-feedback-Teaching-learners-to-see Chapter.pdf"),
    ]


def test_main_prints_exception_messages_when_directory_rebuild_raises_exception_group_without_recorded_failed_files(
    rebuild_index_module,
):
    rebuild_index_module.USE_MANIFEST = True
    rebuild_index_module.ALLOWED_PATHS = {"paper_a.pdf"}
    rebuild_index_module.get_indexed_doc_count = mock.Mock(side_effect=[3, 3])
    rebuild_index_module.get_failed_files = mock.Mock(return_value=[])
    rebuild_index_module.get_directory_index = mock.AsyncMock(
        side_effect=ExceptionGroup(
            "unhandled errors in a TaskGroup",
            [
                LookupError("unknown encoding: /SymbolSetEncoding"),
                ValueError("bad metadata"),
            ],
        )
    )

    with mock.patch("builtins.print") as print_mock:
        asyncio.run(rebuild_index_module.main())

    assert print_mock.call_args_list == [
        mock.call("Manifest PDFs: 1"),
        mock.call("Indexed before run: 3"),
        mock.call("Rebuild completed with parser/indexing errors before any failed PDFs were recorded."),
        mock.call("ERROR: unknown encoding: /SymbolSetEncoding"),
        mock.call("ERROR: bad metadata"),
        mock.call("Indexed after run: 3"),
        mock.call("Failed PDFs: 0"),
    ]


def test_summarize_exception_messages_returns_single_message_for_non_group_exception(rebuild_index_module):
    assert rebuild_index_module.summarize_exception_messages(ValueError("bad metadata")) == ["bad metadata"]


def test_summarize_exception_messages_flattens_nested_exception_groups_in_order(rebuild_index_module):
    nested_group = ExceptionGroup(
        "outer",
        [
            LookupError("unknown encoding: /SymbolSetEncoding"),
            ExceptionGroup("inner", [ValueError("bad metadata")]),
        ],
    )

    assert rebuild_index_module.summarize_exception_messages(nested_group) == [
        "unknown encoding: /SymbolSetEncoding",
        "bad metadata",
    ]
