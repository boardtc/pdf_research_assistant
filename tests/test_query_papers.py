import importlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def query_papers_module():
    sys.modules.pop("query_papers", None)
    module = importlib.import_module("query_papers")
    yield module
    sys.modules.pop("query_papers", None)


def test_main_returns_zero_when_user_quits_immediately(query_papers_module):
    # Mock input so the CLI loop follows the immediate-exit branch.
    with mock.patch("builtins.input", return_value="quit"):
        exit_code = query_papers_module.main()

    assert exit_code == 0


def test_main_prints_subprocess_error_message_when_helper_fails_without_stdout(query_papers_module):
    result = SimpleNamespace(returncode=1, stdout="   ", stderr="helper failed")

    # Mock input so the loop processes one question and then exits cleanly.
    with mock.patch("builtins.input", side_effect=["question", "quit"]):
        # Mock subprocess.run so the test can drive the non-zero-returncode branch without spawning a helper.
        with mock.patch.object(query_papers_module.subprocess, "run", return_value=result):
            # Mock print so the test can assert on the CLI error output.
            with mock.patch("builtins.print") as print_mock:
                exit_code = query_papers_module.main()

    assert exit_code == 0
    assert print_mock.call_args_list == [mock.call("\nQuery failed."), mock.call("helper failed")]


def test_main_prints_generic_failure_only_when_helper_fails_without_stdout_or_stderr(query_papers_module):
    result = SimpleNamespace(returncode=1, stdout="   ", stderr="   ")

    # Mock input so the loop processes one question and then exits cleanly.
    with mock.patch("builtins.input", side_effect=["question", "quit"]):
        # Mock subprocess.run so the test can drive the empty-error-output branch.
        with mock.patch.object(query_papers_module.subprocess, "run", return_value=result):
            # Mock print so the test can assert that only the generic failure line is shown.
            with mock.patch("builtins.print") as print_mock:
                exit_code = query_papers_module.main()

    assert exit_code == 0
    assert print_mock.call_args_list == [mock.call("\nQuery failed.")]


def test_main_prints_stderr_when_stdout_is_not_json_and_stderr_is_present(query_papers_module):
    result = SimpleNamespace(returncode=0, stdout="not json", stderr="better error")

    # Mock input so the loop processes one question and then exits cleanly.
    with mock.patch("builtins.input", side_effect=["question", "quit"]):
        # Mock subprocess.run so the test can reach the JSON decode error branch.
        with mock.patch.object(query_papers_module.subprocess, "run", return_value=result):
            # Mock print so the test can assert that stderr takes precedence after decode failure.
            with mock.patch("builtins.print") as print_mock:
                exit_code = query_papers_module.main()

    assert exit_code == 0
    assert print_mock.call_args_list == [mock.call("\nQuery failed."), mock.call("better error")]


def test_main_prints_stdout_when_stdout_is_not_json_and_stderr_is_empty(query_papers_module):
    result = SimpleNamespace(returncode=0, stdout="plain text failure", stderr="   ")

    # Mock input so the loop processes one question and then exits cleanly.
    with mock.patch("builtins.input", side_effect=["question", "quit"]):
        # Mock subprocess.run so the test can reach the stdout-fallback branch after decode failure.
        with mock.patch.object(query_papers_module.subprocess, "run", return_value=result):
            # Mock print so the test can assert on the displayed fallback output.
            with mock.patch("builtins.print") as print_mock:
                exit_code = query_papers_module.main()

    assert exit_code == 0
    assert print_mock.call_args_list == [mock.call("\nQuery failed."), mock.call("plain text failure")]


def test_main_prints_generic_failure_when_stdout_is_empty_json_decode_fails_and_stderr_is_empty(query_papers_module):
    result = SimpleNamespace(returncode=0, stdout="", stderr="   ")

    # Mock input so the loop processes one question and then exits cleanly.
    with mock.patch("builtins.input", side_effect=["question", "quit"]):
        # Mock subprocess.run so the test can reach the decode-error branch with no fallback message text.
        with mock.patch.object(query_papers_module.subprocess, "run", return_value=result):
            # Mock print so the test can assert that only the generic failure line is shown.
            with mock.patch("builtins.print") as print_mock:
                exit_code = query_papers_module.main()

    assert exit_code == 0
    assert print_mock.call_args_list == [mock.call("\nQuery failed.")]


def test_main_prints_answer_when_payload_is_successful(query_papers_module):
    result = SimpleNamespace(
        returncode=0,
        stdout=json.dumps({"ok": True, "answer": "Answer text"}),
        stderr="",
    )

    # Mock input so the loop processes one question and then exits cleanly.
    with mock.patch("builtins.input", side_effect=["question", "quit"]):
        # Mock subprocess.run so the test can drive the successful payload branch.
        with mock.patch.object(query_papers_module.subprocess, "run", return_value=result):
            # Mock print so the test can assert on the displayed answer.
            with mock.patch("builtins.print") as print_mock:
                exit_code = query_papers_module.main()

    assert exit_code == 0
    assert print_mock.call_args_list == [mock.call("\nAnswer text")]


def test_main_prints_answer_when_nonzero_returncode_still_includes_successful_json_payload(query_papers_module):
    result = SimpleNamespace(
        returncode=1,
        stdout=json.dumps({"ok": True, "answer": "Recovered answer"}),
        stderr="helper complained",
    )

    # Mock input so the loop processes one question and then exits cleanly.
    with mock.patch("builtins.input", side_effect=["question", "quit"]):
        # Mock subprocess.run so the test can show that stdout payload wins when it is present and valid JSON.
        with mock.patch.object(query_papers_module.subprocess, "run", return_value=result):
            # Mock print so the test can assert on the displayed recovered answer.
            with mock.patch("builtins.print") as print_mock:
                exit_code = query_papers_module.main()

    assert exit_code == 0
    assert print_mock.call_args_list == [mock.call("\nRecovered answer")]


def test_main_prints_payload_error_type_and_message_when_payload_is_not_ok(query_papers_module):
    result = SimpleNamespace(
        returncode=0,
        stdout=json.dumps({"ok": False, "error_type": "ValueError", "error": "bad payload"}),
        stderr="",
    )

    # Mock input so the loop processes one question and then exits cleanly.
    with mock.patch("builtins.input", side_effect=["question", "quit"]):
        # Mock subprocess.run so the test can drive the application-level error branch.
        with mock.patch.object(query_papers_module.subprocess, "run", return_value=result):
            # Mock print so the test can assert on the rendered error summary.
            with mock.patch("builtins.print") as print_mock:
                exit_code = query_papers_module.main()

    assert exit_code == 0
    assert print_mock.call_args_list == [mock.call("\nValueError: bad payload")]


def test_main_defaults_error_type_and_message_when_error_payload_fields_are_missing(query_papers_module):
    result = SimpleNamespace(
        returncode=0,
        stdout=json.dumps({"ok": False}),
        stderr="",
    )

    # Mock input so the loop processes one question and then exits cleanly.
    with mock.patch("builtins.input", side_effect=["question", "quit"]):
        # Mock subprocess.run so the test can drive the fallback error formatting branch.
        with mock.patch.object(query_papers_module.subprocess, "run", return_value=result):
            # Mock print so the test can assert on the default error summary.
            with mock.patch("builtins.print") as print_mock:
                exit_code = query_papers_module.main()

    assert exit_code == 0
    assert print_mock.call_args_list == [mock.call("\nError: Unknown error")]
