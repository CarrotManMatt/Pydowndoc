"""Python wrapper for converting/reducing AsciiDoc files back to Markdown."""

import importlib.resources
import itertools
import shlex
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from . import _utils

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from subprocess import CompletedProcess
    from typing import Literal

__all__: "Sequence[str]" = ("run", "run_with_sys_argv")


def run(
    *in_file_paths: Path,
    attributes: "Mapping[str, str] | None" = None,
    output: "Path | Literal['-'] | None" = None,
    postpublish: bool = False,
    prepublish: bool = False,
    display_help: bool = False,
    display_version: bool = False,
    process_capture_output: bool = False,
    process_check_return_code: bool = False,
) -> "CompletedProcess[bytes]":
    """
    Execute the downdoc converter upon the given input files.

    Arguments:
        *in_file_paths: Selection of file paths to convert from AsciiDoc to Markdown.
        attributes: AsciiDoc attributes to be set while rendering AsciiDoc files.
        output: The location to save the converted Markdown output, or `-` to send to stdout.
        postpublish: Whether to run the postpublish lifecycle routine (restore the input file).
        prepublish: Whether to run the prepublish lifecycle routine
            (convert and hide the input file).
        display_help: Whether to skip all conversions and instead display the help text
            to stdout.
        display_version: Whether to skip all conversions and instead display the version
            to stdout.
        process_capture_output: Whether to capture, into a string,
            anything sent to stdout by the subprocess, during execution.
        process_check_return_code: Whether to raise an exception
            if the subprocess exited with a non-zero exit code.

    Returns:
        The details about the completed subprocess execution of the Markdown conversion.

    Raises:
        subprocess.CalledProcessError: Only if `process_check_return_code` is `True`
            and the subprocess exited with a non-zero exit code.
    """
    if attributes is None:
        attributes = {}

    arguments: list[str] = list(
        itertools.chain.from_iterable(
            ("--attribute", shlex.quote(f"{name}={val}")) for name, val in attributes.items()
        )
    )

    if output is not None:
        arguments.extend(("--output", shlex.quote(str(output))))

    if postpublish:
        arguments.append("--postpublish")
    if prepublish:
        arguments.append("--prepublish")
    if display_help:
        arguments.append("--help")
    if display_version:
        arguments.append("--version")

    arguments.extend(shlex.quote(str(in_file_path)) for in_file_path in in_file_paths)

    return _call_binary_with_arguments(
        arguments, capture_output=process_capture_output, check=process_check_return_code
    )


def run_with_sys_argv() -> int:
    """Execute the conversion subprocess with the exact args held by `sys.argv`."""
    return _call_binary_with_arguments(
        sys.argv[1:], capture_output=False, check=False
    ).returncode


def _call_binary_with_arguments(
    arguments: "Sequence[str]", *, capture_output: bool = False, check: bool = False
) -> "CompletedProcess[bytes]":
    if importlib.resources.is_resource("pydowndoc", "downdoc-binary"):
        downdoc_binary_path: Path
        with importlib.resources.path("pydowndoc", "downdoc-binary") as downdoc_binary_path:
            return subprocess.run(
                (downdoc_binary_path, *arguments), check=check, capture_output=capture_output
            )

    return subprocess.run(
        (
            Path(__file__).parent.parent
            / (
                "downloads/downdoc-"
                f"{_utils.get_downdoc_binary_operating_system()}-"
                f"{_utils.get_downdoc_binary_architecture()}"
                f"{_utils.get_downdoc_binary_file_extension()}"
            ),
            *arguments,
        ),
        check=check,
        capture_output=capture_output,
    )
