"""Python wrapper for converting/reducing AsciiDoc files back to Markdown."""

import itertools
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from subprocess import CompletedProcess
    from typing import Final, Literal, Union

__all__: "Sequence[str]" = ("run",)


def _get_downdoc_executable() -> str:
    downdoc_executable: Union[str, None] = shutil.which("downdoc")

    if downdoc_executable is None:
        DOWNDOC_NOT_INSTALLED_MESSAGE: Final[str] = (
            "The downdoc executable could not be found. "
            "Ensure it is installed (E.g `uv add Pydowndoc[bin]`). "
        )
        raise OSError(DOWNDOC_NOT_INSTALLED_MESSAGE)

    return downdoc_executable


def get_help() -> str:
    """
    Retrieve downdoc help text output.

    Returns:
        downdoc's help text output.

    Raises:
        subprocess.CalledProcessError: If calling the downdoc subprocess exited
            with a non-zero exit code.
    """
    return subprocess.run(
        (_get_downdoc_executable(), "--help"), check=True, capture_output=True
    ).stdout.decode()


def get_version() -> str:
    """
    Retrieve the current downdoc version.

    Returns:
        downdoc's version text output.

    Raises:
        subprocess.CalledProcessError: If calling the downdoc subprocess exited
            with a non-zero exit code.
    """
    return subprocess.run(
        (_get_downdoc_executable(), "--version"), check=True, capture_output=True
    ).stdout.decode()


def run(
    *in_file_paths: "Path",
    attributes: "Mapping[str, str] | None" = None,
    output: "Path | Literal['-'] | None" = None,
    postpublish: bool = False,
    prepublish: bool = False,
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

    arguments.append("--")

    arguments.extend(str(in_file_path) for in_file_path in in_file_paths)

    return subprocess.run(
        (_get_downdoc_executable(), *arguments),
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
