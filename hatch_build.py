"""Project build script to package binary artefacts into platform-specific builds."""

import platform
import re
import stat
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, override

from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from hatchling.builders.wheel import WheelBuilder, WheelBuilderConfig

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from typing import Final, Protocol

    from hatchling.builders.config import BuilderConfig
    from hatchling.builders.plugin.interface import BuilderInterface
    from hatchling.plugin.manager import PluginManager

__all__: "Sequence[str]" = ("MultiArtefactWheelBuilder", "get_builder")


if TYPE_CHECKING:

    class _ProtocolBuildFunc(Protocol):
        def __call__(self, directory: str, **build_data: object) -> str: ...


class MultiArtefactWheelBuilder(WheelBuilder):
    """Build multiple wheels at once with each set of binary executables."""

    class _BuildHook(BuildHookInterface[WheelBuilderConfig]):
        @override
        def initialize(self, version: str, build_data: dict[str, object]) -> None:
            downdoc_binary_filepath: Path = Path(self.root) / (
                "downloads/downdoc-"
                f"{_get_downdoc_binary_operating_system()}-"
                f"{_get_downdoc_binary_architecture()}"
                f"{_get_downdoc_binary_file_extension()}"
            )

            if not downdoc_binary_filepath.is_file():
                raise FileNotFoundError(downdoc_binary_filepath)

            downdoc_binary_filepath.chmod(
                downdoc_binary_filepath.stat().st_mode | stat.S_IEXEC
            )

            existing_shared_scripts: object | dict[str, str] = build_data.get(
                "shared_scripts", {}
            )
            if not isinstance(existing_shared_scripts, Mapping):
                raise TypeError

            build_data["shared_scripts"] = {
                str(downdoc_binary_filepath.resolve()): "downdoc",
                **existing_shared_scripts,
            }

    @override
    def get_build_hooks(
        self, directory: str
    ) -> dict[str, BuildHookInterface[WheelBuilderConfig]]:
        return {
            "custom": self._BuildHook(
                self.root,
                {},
                self.config,
                self.metadata,
                directory,
                self.PLUGIN_NAME,
                self.app,
            ),
            **super().get_build_hooks(directory),
        }

    @override
    def get_default_build_data(self) -> dict[str, object]:
        return {
            "dependencies": [],
            "extra_metadata": {},
            "shared_data": {},
            "shared_scripts": {},
        }

    @override
    def get_best_matching_tag(self) -> str:
        tag_match: re.Match[str] | None = re.fullmatch(
            r"\A[^-]+-[^-]+-(?P<platform>.+)\Z", super().get_best_matching_tag()
        )
        if tag_match is None:
            INVALID_BUILD_TAG_MESSAGE: Final[str] = "No build tag match"
            raise ValueError(INVALID_BUILD_TAG_MESSAGE)

        return f"py3-none-{tag_match.group("platform")}"

    @override
    def build_editable_explicit(self, directory: str, **build_data: object) -> str:
        raise NotImplementedError

    @override
    def build_editable_detection(self, directory: str, **build_data: object) -> str:
        raise NotImplementedError

    @override
    def build_editable(self, directory: str, **build_data: object) -> str:
        raise NotImplementedError

    @override
    def get_version_api(self) -> dict[str, "_ProtocolBuildFunc"]:
        return {"standard": self.build_standard}

    @override
    def build_standard(self, directory: str, **build_data: object) -> str:
        build_data["infer_tag"] = True
        build_data["pure_python"] = False

        return super().build_standard(directory, **build_data)


def get_builder() -> (
    "type[BuilderInterface[BuilderConfig, PluginManager]] | "
    "Iterable[type[BuilderInterface[BuilderConfig, PluginManager]]]"
):
    """Retrieve the correct hatch builder hook class."""
    return MultiArtefactWheelBuilder


def _get_downdoc_binary_operating_system() -> str:
    """Retriee the string representation of the current operating system."""
    raw_operating_system: str = sys.platform

    if "linux" in raw_operating_system:
        return "linux"

    if "darwin" in raw_operating_system or "macos" in raw_operating_system:
        return "macos"

    if "win" in raw_operating_system and "darwin" not in raw_operating_system:
        return "win"

    raise NotImplementedError(raw_operating_system)


def _get_downdoc_binary_architecture() -> str:
    """Retreive the string representation of the current platform architecture."""
    raw_architecture: str = platform.machine()

    if "arm64" in raw_architecture:
        return "arm64"

    if "x86_64" in raw_architecture:
        return "x64"

    raise NotImplementedError(raw_architecture)


def _get_downdoc_binary_file_extension() -> str:
    """Retrive the file extension for the executable on the current operating system."""
    raw_operating_system: str = sys.platform

    if "win" in raw_operating_system and "darwin" not in raw_operating_system:
        return ".exe"

    return ""
