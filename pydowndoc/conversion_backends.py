"""Conversion backend classes relating to alternative executable conversion programs."""

import abc
import itertools
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, final, overload

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

from typed_classproperties import classproperty

from ._utils import OUTPUT_CONVERSION_TO_STRING

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence
    from typing import Final, NoReturn

    if sys.version_info >= (3, 11):
        from typing import LiteralString
    else:
        from typing_extensions import LiteralString

    from ._utils import ConversionOutputDestinationFlag

__all__: "Sequence[str]" = (
    "BaseConversionBackend",
    "DowndocMarkdownConversionBackend",
    "PandocMarkdownConversionBackend",
    "PandocMultiMarkdownConversionBackend",
    "PandocPHPMarkdownExtraConversionBackend",
    "PandocRSTConversionBackend",
    "PandocTXTConversionBackend",
)


class BaseConversionBackend(abc.ABC):
    """Abstract base class defining the structural API of a conversion backend."""

    @classproperty
    @abc.abstractmethod
    def ID(cls) -> "LiteralString":  # noqa: D102, N802
        pass

    @classmethod
    @abc.abstractmethod
    def get_version(cls) -> str:
        """Retrieve the version of the executable used by this conversion backend."""

    @classmethod
    @abc.abstractmethod
    def _convert_string(
        cls, asciidoc_content: str, *, attributes: "Mapping[str, str] | None" = None
    ) -> str:
        pass

    @final
    @classmethod
    def convert_string(
        cls, asciidoc_content: str, *, attributes: "Mapping[str, str] | None" = None
    ) -> str:
        """Convert AsciiDoc string content to an interpretable documentation format."""
        if not asciidoc_content.strip():
            INVALID_ASCIIDOC_CONTENT_MESSAGE: Final[str] = (
                "Cannot convert empty string content."
            )
            raise ValueError(INVALID_ASCIIDOC_CONTENT_MESSAGE)

        return cls._convert_string(asciidoc_content=asciidoc_content, attributes=attributes)

    @overload
    @classmethod
    @abc.abstractmethod
    def _convert_file(
        cls,
        file_path: "Path",
        *,
        output_location: "ConversionOutputDestinationFlag",
        attributes: "Mapping[str, str] | None" = ...,
        postpublish: bool = ...,
        prepublish: bool = ...,
    ) -> str: ...

    @overload
    @classmethod
    @abc.abstractmethod
    def _convert_file(
        cls,
        file_path: "Path",
        *,
        attributes: "Mapping[str, str] | None" = ...,
        output_location: "Path | None" = ...,
        postpublish: bool = ...,
        prepublish: bool = ...,
    ) -> None: ...

    @classmethod
    @abc.abstractmethod
    def _convert_file(
        cls,
        file_path: "Path",
        *,
        attributes: "Mapping[str, str] | None" = None,
        output_location: "Path | ConversionOutputDestinationFlag | None" = None,
        postpublish: bool = False,
        prepublish: bool = False,
    ) -> "str | None":
        pass

    @overload
    @classmethod
    def convert_file(
        cls,
        file_path: "Path",
        *,
        output_location: "ConversionOutputDestinationFlag",
        attributes: "Mapping[str, str] | None" = ...,
        postpublish: bool = ...,
        prepublish: bool = ...,
    ) -> str: ...

    @overload
    @classmethod
    def convert_file(
        cls,
        file_path: "Path",
        *,
        attributes: "Mapping[str, str] | None" = ...,
        output_location: "Path | None" = ...,
        postpublish: bool = ...,
        prepublish: bool = ...,
    ) -> None: ...

    @final
    @classmethod
    def convert_file(
        cls,
        file_path: "Path",
        *,
        attributes: "Mapping[str, str] | None" = None,
        output_location: "Path | ConversionOutputDestinationFlag | None" = None,
        postpublish: bool = False,
        prepublish: bool = False,
    ) -> "str | None":
        """Convert an AsciiDoc file to an interpretable documentation format."""
        if not file_path.is_file():
            raise FileNotFoundError(file_path)

        return cls._convert_file(
            file_path=file_path,
            attributes=attributes,
            output_location=output_location,
            postpublish=postpublish,
            prepublish=prepublish,
        )

    @classmethod
    def _attributes_to_arguments(
        cls, attributes: "Mapping[str, str] | None"
    ) -> "Iterable[str]":
        if attributes is None:
            attributes = {}

        return itertools.chain.from_iterable(
            ("--attribute", f"{shlex.quote(name)}={shlex.quote(val)}")
            for name, val in attributes.items()
        )

    if not TYPE_CHECKING:

        @override
        def __new__(cls) -> "NoReturn":
            CANNOT_INSTANTIATE_OBJECTS_MESSAGE: Final[str] = (
                "Cannot instantiate objects of this type."
            )
            raise RuntimeError(CANNOT_INSTANTIATE_OBJECTS_MESSAGE)


class DowndocMarkdownConversionBackend(BaseConversionBackend):
    """Backend to convert AsciiDoc content to Markdown using downdoc."""

    @classproperty
    @override
    def ID(cls) -> "LiteralString":
        return "downdoc-md"

    @classmethod
    def _get_downdoc_executable_path(cls) -> str:
        downdoc_executable: "str | None" = shutil.which("downdoc")

        if downdoc_executable is None:
            DOWNDOC_NOT_INSTALLED_MESSAGE: Final[str] = (
                "The downdoc executable could not be found. "
                "Ensure it is installed (E.g `uv add Pydowndoc[bin]`)."
            )
            raise OSError(DOWNDOC_NOT_INSTALLED_MESSAGE)

        return downdoc_executable

    @classmethod
    @override
    def get_version(cls) -> str:
        return subprocess.run(
            (cls._get_downdoc_executable_path(), "--version"),
            check=True,
            text=True,
            capture_output=True,
        ).stdout.strip()

    @classmethod
    @override
    def _convert_string(
        cls, asciidoc_content: str, *, attributes: "Mapping[str, str] | None" = None
    ) -> str:
        ends_with_newline: bool = asciidoc_content.endswith("\n")

        converted_string: str = subprocess.run(
            (
                cls._get_downdoc_executable_path(),
                *cls._attributes_to_arguments(attributes),
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

    @overload
    @classmethod
    @override
    def _convert_file(
        cls,
        file_path: "Path",
        *,
        output_location: "ConversionOutputDestinationFlag",
        attributes: "Mapping[str, str] | None" = ...,
        postpublish: bool = ...,
        prepublish: bool = ...,
    ) -> str: ...

    @overload
    @classmethod
    @override
    def _convert_file(
        cls,
        file_path: "Path",
        *,
        attributes: "Mapping[str, str] | None" = ...,
        output_location: "Path | None" = ...,
        postpublish: bool = ...,
        prepublish: bool = ...,
    ) -> None: ...

    @classmethod
    @override
    def _convert_file(
        cls,
        file_path: "Path",
        *,
        attributes: "Mapping[str, str] | None" = None,
        output_location: "Path | ConversionOutputDestinationFlag | None" = None,
        postpublish: bool = False,
        prepublish: bool = False,
    ) -> "str | None":
        optional_arguments: list[str] = []

        if output_location == OUTPUT_CONVERSION_TO_STRING:
            optional_arguments.extend(("--output", "-"))
        elif isinstance(output_location, Path):
            optional_arguments.extend(("--output", str(output_location)))

        if postpublish:
            optional_arguments.extend("--postpublish")
        if prepublish:
            optional_arguments.extend("--prepublish")

        subprocess_stdout: str = subprocess.run(
            (
                cls._get_downdoc_executable_path(),
                *cls._attributes_to_arguments(attributes),
                *optional_arguments,
                "--",
                str(file_path),
            ),
            check=True,
            text=True,
            capture_output=True,
        ).stdout

        return subprocess_stdout if output_location == OUTPUT_CONVERSION_TO_STRING else None


class _BasePandocConversionBackend(BaseConversionBackend, abc.ABC):
    @classproperty
    @abc.abstractmethod
    def PANDOC_ID(cls) -> "LiteralString":  # noqa: N802
        pass

    @classproperty
    @abc.abstractmethod
    def FILE_SUFFIX(cls) -> "LiteralString":  # noqa: N802
        pass

    @classmethod
    def _get_asciidoctor_executable_path(cls) -> str:
        asciidoctor_executable: "str | None" = shutil.which("asciidoctor")

        if asciidoctor_executable is None:
            ASCIIDOCTOR_NOT_INSTALLED_MESSAGE: Final[str] = (
                "The asciidoctor executable could not be found. "
                "Ensure it is installed (https://docs.asciidoctor.org/asciidoctor/latest/install)."
            )
            raise OSError(ASCIIDOCTOR_NOT_INSTALLED_MESSAGE)

        return asciidoctor_executable

    @classmethod
    def _get_pandoc_executable_path(cls) -> str:
        pandoc_executable: "str | None" = shutil.which("pandoc")

        if pandoc_executable is None:
            PANDOC_NOT_INSTALLED_MESSAGE: Final[str] = (
                "The pandoc executable could not be found. "
                "Ensure it is installed (https://pandoc.org/installing.html)."
            )
            raise OSError(PANDOC_NOT_INSTALLED_MESSAGE)

        return pandoc_executable

    @classmethod
    @override
    def get_version(cls) -> str:
        # NOTE: Intermediary variables are used to prevent 'Unterminated f-string literal' errors in older Python versions
        asciidoctor_version: str = subprocess.run(
            (cls._get_asciidoctor_executable_path(), "--version"),
            check=True,
            text=True,
            capture_output=True,
        ).stdout.strip()

        pandoc_version: str = subprocess.run(
            (cls._get_pandoc_executable_path(), "--version"),
            check=True,
            text=True,
            capture_output=True,
        ).stdout.strip()

        return f"{asciidoctor_version}\n{pandoc_version}"

    @classmethod
    @override
    def _convert_string(
        cls, asciidoc_content: str, *, attributes: "Mapping[str, str] | None" = None
    ) -> str:
        return subprocess.run(
            (
                cls._get_pandoc_executable_path(),
                "--from",
                "docbook",
                "--to",
                cls.PANDOC_ID,
                "--output",
                "-",
                "--fail-if-warnings",
            ),
            check=True,
            input=(
                subprocess.run(
                    (
                        cls._get_asciidoctor_executable_path(),
                        *cls._attributes_to_arguments(attributes),
                        "--out-file",
                        "-",
                        "--backend",
                        "docbook5",
                        "--warnings",
                        "--failure-level",
                        "WARNING",
                        "--",
                        "-",
                    ),
                    check=True,
                    input=asciidoc_content,
                    text=True,
                    capture_output=True,
                ).stdout
            ),
            text=True,
            capture_output=True,
        ).stdout

    @overload
    @classmethod
    @override
    def _convert_file(
        cls,
        file_path: "Path",
        *,
        output_location: "ConversionOutputDestinationFlag",
        attributes: "Mapping[str, str] | None" = ...,
        postpublish: bool = ...,
        prepublish: bool = ...,
    ) -> str: ...

    @overload
    @classmethod
    @override
    def _convert_file(
        cls,
        file_path: "Path",
        *,
        attributes: "Mapping[str, str] | None" = ...,
        output_location: "Path | None" = ...,
        postpublish: bool = ...,
        prepublish: bool = ...,
    ) -> None: ...

    @classmethod
    @override
    def _convert_file(
        cls,
        file_path: "Path",
        *,
        attributes: "Mapping[str, str] | None" = None,
        output_location: "Path | ConversionOutputDestinationFlag | None" = None,
        postpublish: bool = False,
        prepublish: bool = False,
    ) -> "str | None":
        if postpublish or prepublish:
            INVALID_PREPUBLISH_OR_POSTPUBLISH_MESSAGE: Final[str] = (
                "Neither 'postpublish' nor 'prepublish' can be used "
                "for this conversion backend."
            )
            raise ValueError(INVALID_PREPUBLISH_OR_POSTPUBLISH_MESSAGE)

        optional_arguments: list[str] = []

        if output_location is None:
            optional_arguments.extend(
                ("--output", str(file_path.with_suffix(cls.FILE_SUFFIX)))
            )
        elif output_location == OUTPUT_CONVERSION_TO_STRING:
            optional_arguments.extend(("--output", "-"))
        elif isinstance(output_location, Path):
            optional_arguments.extend(("--output", str(output_location)))

        subprocess_stdout: str = subprocess.run(
            (
                cls._get_pandoc_executable_path(),
                "--from",
                "docbook",
                "--to",
                cls.PANDOC_ID,
                *optional_arguments,
                "--fail-if-warnings",
            ),
            check=True,
            input=(
                subprocess.run(
                    (
                        cls._get_asciidoctor_executable_path(),
                        *cls._attributes_to_arguments(attributes),
                        "--out-file",
                        "-",
                        "--backend",
                        "docbook5",
                        "--warnings",
                        "--failure-level",
                        "WARNING",
                        "--",
                        str(file_path),
                    ),
                    check=True,
                    text=True,
                    capture_output=True,
                ).stdout
            ),
            text=True,
            capture_output=True,
        ).stdout

        return subprocess_stdout if output_location == OUTPUT_CONVERSION_TO_STRING else None


class PandocMarkdownConversionBackend(_BasePandocConversionBackend):
    """Backend to convert AsciiDoc content to Pandoc's Markdown using pandoc & Asciidoctor."""

    @classproperty
    @override
    def ID(cls) -> "LiteralString":
        return "pandoc-md"

    @classproperty
    @override
    def PANDOC_ID(cls) -> "LiteralString":
        return "markdown"

    @classproperty
    @override
    def FILE_SUFFIX(cls) -> "LiteralString":
        return ".md"


class PandocMultiMarkdownConversionBackend(_BasePandocConversionBackend):
    """Backend to convert AsciiDoc content to MultiMarkdown using pandoc & Asciidoctor."""

    @classproperty
    @override
    def ID(cls) -> "LiteralString":
        return "pandoc-multi-md"

    @classproperty
    @override
    def PANDOC_ID(cls) -> "LiteralString":
        return "markdown_mmd"

    @classproperty
    @override
    def FILE_SUFFIX(cls) -> "LiteralString":
        return ".md"


class PandocPHPMarkdownExtraConversionBackend(_BasePandocConversionBackend):
    """Backend to convert AsciiDoc content to PHP Markdown Extra using pandoc & Asciidoctor."""

    @classproperty
    @override
    def ID(cls) -> "LiteralString":
        return "pandoc-php-md-extra"

    @classproperty
    @override
    def PANDOC_ID(cls) -> "LiteralString":
        return "markdown_phpextra"

    @classproperty
    @override
    def FILE_SUFFIX(cls) -> "LiteralString":
        return ".md"


class PandocTXTConversionBackend(_BasePandocConversionBackend):
    """Backend to convert AsciiDoc content to plaintext using pandoc & Asciidoctor."""

    @classproperty
    @override
    def ID(cls) -> "LiteralString":
        return "pandoc-txt"

    @classproperty
    @override
    def PANDOC_ID(cls) -> "LiteralString":
        return "plain"

    @classproperty
    @override
    def FILE_SUFFIX(cls) -> "LiteralString":
        return ".txt"


class PandocRSTConversionBackend(_BasePandocConversionBackend):
    """Backend to convert AsciiDoc content to reStructuredText using pandoc & Asciidoctor."""

    @classproperty
    @override
    def ID(cls) -> "LiteralString":
        return "pandoc-rst"

    @classproperty
    @override
    def PANDOC_ID(cls) -> "LiteralString":
        return "rst"

    @classproperty
    @override
    def FILE_SUFFIX(cls) -> "LiteralString":
        return ".rst"
