"""Python wrapper for converting/reducing AsciiDoc files back to Markdown."""

import itertools
import shlex
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from subprocess import CompletedProcess
    from typing import Literal

__all__: "Sequence[str]" = ("run",)


def run(
    *in_file_paths: "Path",
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
            ("--attribute", f"{shlex.quote(name)}={shlex.quote(val)}")
            for name, val in attributes.items()
        )
    )

    if output is not None:
        arguments.extend(("--output", str(output)))

    if postpublish:
        arguments.append("--postpublish")
    if prepublish:
        arguments.append("--prepublish")
    if display_help:
        arguments.append("--help")
    if display_version:
        arguments.append("--version")

    arguments.append("--")

    arguments.extend(str(in_file_path) for in_file_path in in_file_paths)

    return subprocess.run(
        ("downdoc", *arguments),
        check=process_check_return_code,
        capture_output=process_capture_output,
    )


def run_with_sys_argv() -> int:
    """Execute the conversion subprocess with the exact args held by `sys.argv`."""
    return run(
        *(Path(argument) for argument in sys.argv[1:]),
        process_capture_output=False,
        process_check_return_code=False,
    ).returncode
