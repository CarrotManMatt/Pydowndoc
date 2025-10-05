"""
Hatch build package hooks entry-points.

Convert your AsciiDoc README to the Markdown format, supported by PyPA's README specification:
https://packaging.python.org/en/latest/specifications/pyproject-toml/#readme
"""

import inspect
import sys
from collections.abc import Collection, Iterable
from pathlib import Path
from typing import TYPE_CHECKING

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

from hatchling.metadata.plugin.interface import MetadataHookInterface
from hatchling.plugin import hookimpl
from typed_classproperties import classproperty

import pydowndoc
from pydowndoc.conversion_backends import (
    DowndocMarkdownConversionBackend,
    PandocMarkdownConversionBackend,
    PandocMultiMarkdownConversionBackend,
    PandocPHPMarkdownExtraConversionBackend,
    PandocRSTConversionBackend,
    PandocTXTConversionBackend,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from typing import Final

    from pydowndoc.conversion_backends import BaseConversionBackend

__all__: "Sequence[str]" = ("DowndocReadmeMetadataHook", "hatch_register_metadata_hook")


class DowndocReadmeMetadataHook(MetadataHookInterface):
    """Hatchling metadata hook for converting AsciiDoc README files to Markdown format."""

    @classproperty
    @override
    def PLUGIN_NAME(cls) -> str:
        return "downdoc-readme"

    @classmethod
    def _get_readme_path(cls, config: "Mapping[str, object]", root: Path) -> Path:
        raw_readme_path: "object | str" = config.get("path", "")

        if not isinstance(raw_readme_path, str):
            INVALID_PATH_TYPE_MESSAGE: Final[str] = f"{cls.PLUGIN_NAME}.path must be a string."
            raise TypeError(INVALID_PATH_TYPE_MESSAGE)

        return root / (raw_readme_path if raw_readme_path else "README.adoc")

    @classmethod
    def _get_conversion_backend(
        cls, config: "Mapping[str, object]"
    ) -> "type[BaseConversionBackend] | None":
        raw_conversion_backend: "object | str" = config.get("backend", "")

        if not isinstance(raw_conversion_backend, str):
            INVALID_CONVERSION_BACKEND_TYPE_MESSAGE: Final[str] = (
                f"{cls.PLUGIN_NAME}.backend must be a string."
            )
            raise TypeError(INVALID_CONVERSION_BACKEND_TYPE_MESSAGE)

        raw_conversion_backend = raw_conversion_backend.strip()

        if not raw_conversion_backend:
            return None

        try:
            return {
                conversion_backend.ID: conversion_backend
                for conversion_backend in (
                    DowndocMarkdownConversionBackend,
                    PandocMarkdownConversionBackend,
                    PandocMultiMarkdownConversionBackend,
                    PandocPHPMarkdownExtraConversionBackend,
                    PandocTXTConversionBackend,
                    PandocRSTConversionBackend,
                )
            }[raw_conversion_backend]
        except KeyError as e:
            INVALID_CONVERSION_BACKEND_MESSAGE: Final[str] = (
                f"Invalid conversion_backend: {raw_conversion_backend!r}."
            )
            raise ValueError(INVALID_CONVERSION_BACKEND_MESSAGE) from e

    @classmethod
    def _is_project_misconfigured(cls, metadata: "Mapping[str, object]") -> bool:
        if "readme" in metadata:
            return True

        dynamic: "object | Collection[object]" = metadata.get("dynamic", [])
        if not isinstance(dynamic, Collection):
            INVALID_DYNAMIC_TYPE_MESSAGE: Final[str] = (
                "'dynamic' field within `[project]` must be an array."
            )
            raise TypeError(INVALID_DYNAMIC_TYPE_MESSAGE)

        return "readme" not in dynamic

    @override
    def update(self, metadata: dict[str, object]) -> None:
        if (
            ("update", __file__)
            in ((frame.function, frame.filename) for frame in inspect.stack()[1:])
        ):  # SOURCE: https://github.com/flying-sheep/hatch-docstring-description/blob/2dfbfba2c48e112825fdd0cb7c37035d5598224c/src/hatch_docstring_description/read_description.py#L21
            return

        if self._is_project_misconfigured(metadata):
            MISSING_DYNAMIC_MESSAGE: Final[str] = (
                "You must add 'readme' to your `dynamic` fields and not to `[project]`."
            )
            raise TypeError(MISSING_DYNAMIC_MESSAGE)

        readme_path: Path = self._get_readme_path(self.config, Path(self.root))

        if not readme_path.is_file():
            raise FileNotFoundError(str(readme_path))

        conversion_backend: "type[BaseConversionBackend] | None" = (
            self._get_conversion_backend(self.config)
        )

        metadata["readme"] = {
            "content-type": "text/markdown",
            "text": (
                pydowndoc.convert_file(
                    readme_path,
                    output_location=pydowndoc.OUTPUT_CONVERSION_TO_STRING,
                    backend=conversion_backend,
                )
                if conversion_backend is not None
                else pydowndoc.convert_file(
                    readme_path,
                    output_location=pydowndoc.OUTPUT_CONVERSION_TO_STRING,
                )
            ),
        }

        if isinstance(metadata["dynamic"], Iterable):
            metadata["dynamic"] = [value for value in metadata["dynamic"] if value != "readme"]


@hookimpl
def hatch_register_metadata_hook() -> (
    "type[MetadataHookInterface] | list[type[MetadataHookInterface]]"
):
    """Export the correct metadata hook class for hatch projects."""
    return DowndocReadmeMetadataHook
