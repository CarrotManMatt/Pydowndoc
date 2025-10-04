"""Python wrapper for converting/reducing AsciiDoc files back to Markdown."""

import itertools
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, overload

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence
    from typing import Final, Union

__all__: "Sequence[str]" = (
    "OUTPUT_CONVERSION_TO_STRING",
    "ConversionError",
    "convert_file",
    "convert_string",
    "get_help",
    "get_version",
)


class _ConversionOutputDestinationFlag:
    pass


OUTPUT_CONVERSION_TO_STRING: "Final[_ConversionOutputDestinationFlag]" = (
    _ConversionOutputDestinationFlag()
)


class ConversionError(RuntimeError):
    """Raised when an error occurs while using the downdoc binary in a subprocess."""

    @override
    def __init__(
        self,
        message: str | None = None,
        *,
        subprocess_return_code: int | None = None,
        subprocess_stderr: str | None = None,
    ) -> None:
        self.message: str | None = message
        self.subprocess_return_code: int | None = subprocess_return_code
        self.subprocess_stderr: str | None = subprocess_stderr


def _get_downdoc_executable() -> str:
    downdoc_executable: Union[str, None] = shutil.which("downdoc")

    if downdoc_executable is None:
        DOWNDOC_NOT_INSTALLED_MESSAGE: Final[str] = (
            "The downdoc executable could not be found. "
            "Ensure it is installed (E.g `uv add Pydowndoc[bin]`). "
        )
        raise OSError(DOWNDOC_NOT_INSTALLED_MESSAGE)

    return downdoc_executable


def _attributes_to_arguments(attributes: "Mapping[str, str] | None") -> "Iterable[str]":
    if attributes is None:
        attributes = {}

    return itertools.chain.from_iterable(
        ("--attribute", f"{shlex.quote(name)}={shlex.quote(val)}")
        for name, val in attributes.items()
    )


def get_help() -> str:
    """
    Retrieve the downdoc help text output.

    Returns:
        downdoc's help text output.

    Raises:
        subprocess.CalledProcessError: If calling the downdoc subprocess exited
            with a non-zero exit code.
    """
    return subprocess.run(
        (_get_downdoc_executable(), "--help"), check=True, text=True, capture_output=True
    ).stdout


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
        (_get_downdoc_executable(), "--version"), check=True, text=True, capture_output=True
    ).stdout


@overload
def convert_file(
    file_path: "Path",
    *,
    output_location: _ConversionOutputDestinationFlag,
    attributes: "Mapping[str, str] | None" = ...,
    postpublish: bool = ...,
    prepublish: bool = ...,
) -> str: ...


@overload
def convert_file(
    file_path: "Path",
    *,
    attributes: "Mapping[str, str] | None" = ...,
    output_location: Path | None = ...,
    postpublish: bool = ...,
    prepublish: bool = ...,
) -> None: ...


def convert_file(
    file_path: "Path",
    *,
    attributes: "Mapping[str, str] | None" = None,
    output_location: Path | _ConversionOutputDestinationFlag | None = None,
    postpublish: bool = False,
    prepublish: bool = False,
) -> str | None:
    """
    Execute the downdoc converter upon the given input file path.

    Arguments:
        file_path: The location of the file to convert from AsciiDoc to Markdown.
        attributes: AsciiDoc attributes to be set while rendering AsciiDoc files.
        output_location: The location to save the converted Markdown output,
            or `OUTPUT_CONVERSION_TO_STRING` to return as a string.
            By default (or when `None`), the output file will use the same name
            as the input file, with the extension changed to `.md`.
        postpublish: Whether to run the postpublish lifecycle routine (restore the input file).
        prepublish: Whether to run the prepublish lifecycle routine
            (convert and hide the input file).

    Returns:
        `None`, or the converted Markdown output
        when `output_location` is `OUTPUT_CONVERSION_TO_STRING`.

    Raises:
        ConversionError: When calling the downdoc subprocess exited with an error.
    """
    if not file_path.is_file():
        raise FileNotFoundError(file_path)

    optional_arguments: list[str] = []

    if isinstance(output_location, Path):
        optional_arguments.extend(("--output", str(output_location)))
    elif isinstance(output_location, _ConversionOutputDestinationFlag):
        optional_arguments.extend(("--output", "-"))

    if postpublish:
        optional_arguments.extend("--postpublish")
    if prepublish:
        optional_arguments.extend("--prepublish")

    return subprocess.run(
        (
            _get_downdoc_executable(),
            *_attributes_to_arguments(attributes),
            *optional_arguments,
            "--",
            str(file_path),
        ),
        check=True,
        text=True,
        capture_output=True,
    ).stdout


def convert_string(
    asciidoc_content: str, *, attributes: "Mapping[str, str] | None" = None
) -> str:
    """
    Execute the downdoc converter upon the given AsciiDoc content string.

    Arguments:
        asciidoc_content: The string AsciiDoc content to convert.
        attributes: AsciiDoc attributes to be set while rendering AsciiDoc files.

    Returns:
        The converted Markdown output.

    Raises:
        ConversionError: When calling the downdoc subprocess exited with an error.
    """
    if not asciidoc_content.strip():
        INVALID_ASCIIDOC_CONTENT_MESSAGE: Final[str] = "Cannot convert empty string content."
        raise ValueError(INVALID_ASCIIDOC_CONTENT_MESSAGE)

    ends_with_newline: bool = asciidoc_content.endswith("\n")

    converted_string: str = subprocess.run(
        (
            _get_downdoc_executable(),
            *_attributes_to_arguments(attributes),
            "--output",
            "-",
            "--",
            "-",
        ),
        check=True,
        input=asciidoc_content,
        text=True,
        capture_output=True,
    ).stdout

    return converted_string if ends_with_newline else converted_string.removesuffix("\n")
