"""Python wrapper for converting/reducing AsciiDoc files back to Markdown."""

from typing import TYPE_CHECKING, overload

from ._utils import OUTPUT_CONVERSION_TO_STRING, ConversionError
from .conversion_backends import DowndocMarkdownConversionBackend

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    from ._utils import ConversionOutputDestinationFlag
    from .conversion_backends import BaseConversionBackend

__all__: "Sequence[str]" = (
    "OUTPUT_CONVERSION_TO_STRING",
    "ConversionError",
    "convert_file",
    "convert_string",
    "get_version",
)


def get_version(
    backend: "type[BaseConversionBackend]" = DowndocMarkdownConversionBackend,
) -> str:
    """
    Retrieve the current version of the given conversion backend.

    Arguments:
        backend: The conversion backend to get the version of, defaults to `DOWNDOC_MD`.

    Returns:
        Conversion backend's version text output.

    Raises:
        subprocess.CalledProcessError: If calling the conversion backend subprocess exited
            with a non-zero exit code.
    """
    return backend.get_version()


@overload
def convert_file(
    file_path: "Path",
    *,
    output_location: "ConversionOutputDestinationFlag",
    backend: "type[BaseConversionBackend]" = ...,
    attributes: "Mapping[str, str] | None" = ...,
    postpublish: bool = ...,
    prepublish: bool = ...,
) -> str: ...


@overload
def convert_file(
    file_path: "Path",
    *,
    attributes: "Mapping[str, str] | None" = ...,
    output_location: "Path | None" = ...,
    backend: "type[BaseConversionBackend]" = ...,
    postpublish: bool = ...,
    prepublish: bool = ...,
) -> None: ...


def convert_file(
    file_path: "Path",
    *,
    attributes: "Mapping[str, str] | None" = None,
    output_location: "Path | ConversionOutputDestinationFlag | None" = None,
    backend: "type[BaseConversionBackend]" = DowndocMarkdownConversionBackend,
    postpublish: bool = False,
    prepublish: bool = False,
) -> "str | None":
    """
    Execute the downdoc converter upon the given input file path.

    Arguments:
        file_path: The location of the file to convert from AsciiDoc to Markdown.
        attributes: AsciiDoc attributes to be set while rendering AsciiDoc files.
        output_location: The location to save the converted Markdown output,
            or `OUTPUT_CONVERSION_TO_STRING` to return as a string.
            By default (or when `None`), the output file will use the same name
            as the input file, with the extension changed to `.md`.
        backend: The conversion backend to use, defaults to `downdoc-md`.
        postpublish: Whether to run the postpublish lifecycle routine (restore the input file).
        prepublish: Whether to run the prepublish lifecycle routine
            (convert and hide the input file).

    Returns:
        `None`, or the converted Markdown output
        when `output_location` is `OUTPUT_CONVERSION_TO_STRING`.

    Raises:
        ConversionError: When calling the downdoc subprocess exited with an error.
    """
    return backend.convert_file(
        file_path=file_path,
        attributes=attributes,
        output_location=output_location,
        postpublish=postpublish,
        prepublish=prepublish,
    )


def convert_string(
    asciidoc_content: str,
    *,
    attributes: "Mapping[str, str] | None" = None,
    backend: "type[BaseConversionBackend]" = DowndocMarkdownConversionBackend,
) -> str:
    """
    Execute the downdoc converter upon the given AsciiDoc content string.

    Arguments:
        asciidoc_content: The string AsciiDoc content to convert.
        attributes: AsciiDoc attributes to be set while rendering AsciiDoc files.
        backend: The conversion backend to use, defaults to `downdoc-md`.

    Returns:
        The converted Markdown output.

    Raises:
        ConversionError: When calling the downdoc subprocess exited with an error.
    """
    return backend.convert_string(asciidoc_content=asciidoc_content, attributes=attributes)
