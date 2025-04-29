"""Project build script to package binary artefacts into platform-specific builds."""

import platform
import re
import stat
import subprocess
import sys
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import TYPE_CHECKING, override

import setuptools_scm
from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from hatchling.builders.wheel import WheelBuilder, WheelBuilderConfig
from hatchling.metadata.plugin.interface import MetadataHookInterface
from packaging.version import Version

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Final, Protocol

    from hatchling.builders.config import BuilderConfig
    from hatchling.builders.plugin.interface import BuilderInterface
    from hatchling.plugin.manager import PluginManager

__all__: "Sequence[str]" = (
    "DowndocVersionHook",
    "MultiArtefactWheelBuilder",
    "get_builder",
    "get_metadata_hook",
)


if TYPE_CHECKING:

    class _ProtocolBuildFunc(Protocol):
        def __call__(self, directory: str, **build_data: object) -> str: ...


class DowndocVersionHook(MetadataHookInterface):
    """Hatchling metadata hook for retrieving the project version from the downdoc binary."""

    @override
    def update(self, metadata: dict[str, object]) -> None:
        scm_version: Version = Version(
            setuptools_scm.get_version(
                root=Path(self.root).parent,
                local_scheme="no-local-version",
                version_scheme="no-guess-dev",
            )
        )

        if (
            scm_version.epoch
            or scm_version.pre
            or scm_version.post
            or scm_version.local
            or any(
                part is not None and (part > 999 or part < 1)
                for part in (*scm_version.release, scm_version.dev)
            )
        ):
            VERSION_NUMBER_UNCONVERTABLE_MESSAGE: Final[str] = (
                f"The project version number: {scm_version} is not convertable to an integer "
                "of the downdoc binary's post release version."
            )
            raise NotImplementedError(VERSION_NUMBER_UNCONVERTABLE_MESSAGE)

        bin_version: Version = Version(
            subprocess.run(
                (str(_get_downdoc_binary_filepath(root=Path(self.root))), "--version"),
                capture_output=True,
                text=True,
                check=True,
            )
            .stdout.strip()
            .removesuffix("-stable")
            .strip()
        )

        metadata["version"] = "".join(
            part
            for part in (
                f"{bin_version.epoch}!" if bin_version.epoch != 0 else None,
                ".".join(str(part) for part in bin_version.release),
                (
                    "".join(str(part) for part in bin_version.pre)
                    if bin_version.pre is not None
                    else None
                ),
                f".post{
                    +(scm_version.major * (10**9))
                    + (scm_version.minor * (10**6))
                    + (scm_version.micro * (10**3))
                    + ((scm_version.dev or 0) * (10**0))
                }",
                (f".dev{bin_version.dev}" if bin_version.dev is not None else None),
            )
            if part is not None
        )

        if isinstance(metadata["dynamic"], Iterable):
            metadata["dynamic"] = [
                value for value in metadata["dynamic"] if value != "version"
            ]


def get_metadata_hook() -> "type[MetadataHookInterface] | list[type[MetadataHookInterface]]":
    """Retrieve the correct hatch version metadata hook class."""
    return DowndocVersionHook


class MultiArtefactWheelBuilder(WheelBuilder):
    """Build multiple wheels at once with each set of binary executables."""

    class _BuildHook(BuildHookInterface[WheelBuilderConfig]):
        @override
        def initialize(self, version: str, build_data: dict[str, object]) -> None:
            existing_shared_scripts: object | dict[str, str] = build_data.get(
                "shared_scripts", {}
            )
            if not isinstance(existing_shared_scripts, Mapping):
                raise TypeError

            build_data["shared_scripts"] = {
                str(
                    _get_downdoc_binary_filepath(root=Path(self.root)).resolve()
                ): f"downdoc{_get_downdoc_binary_file_extension()}",
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

        return f"py3-none-{tag_match.group('platform')}"

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
        self.target_config["bypass-selection"] = True

        return super().build_standard(directory, **build_data)


def get_builder() -> (
    "type[BuilderInterface[BuilderConfig, PluginManager]] | "
    "Iterable[type[BuilderInterface[BuilderConfig, PluginManager]]]"
):
    """Retrieve the correct hatch builder hook class."""
    return MultiArtefactWheelBuilder


def _get_downdoc_binary_operating_system() -> str:
    """Retrieve the string representation of the current operating system."""
    raw_operating_system: str = sys.platform

    if "linux" in raw_operating_system:
        return "linux"

    if "darwin" in raw_operating_system or "macos" in raw_operating_system:
        return "macos"

    if "win" in raw_operating_system and "darwin" not in raw_operating_system:
        return "windows"

    raise NotImplementedError(raw_operating_system)


def _get_downdoc_binary_architecture() -> str:
    """Retrieve the string representation of the current platform architecture."""
    raw_architecture: str = platform.machine()

    if "arm64" in raw_architecture:
        return "arm64"

    if (
        "x86_64" in raw_architecture
        or "x64" in raw_architecture
        or "amd64" in raw_architecture.lower()
    ):
        return "x86-64"

    raise NotImplementedError(raw_architecture)


def _get_downdoc_binary_file_extension() -> str:
    """Retrieve the file extension for the executable on the current operating system."""
    raw_operating_system: str = sys.platform

    if "linux" in raw_operating_system:
        return ""

    if "darwin" in raw_operating_system or "macos" in raw_operating_system:
        return ""

    if "win" in raw_operating_system and "darwin" not in raw_operating_system:
        return ".exe"

    raise NotImplementedError(raw_operating_system)


def _get_downdoc_binary_filepath(root: Path) -> Path:
    """Retrieve the file path for the downloaded downdoc binary executable."""
    downdoc_binary_filepath: Path = root / (
        "downloads/downdoc-"
        f"{_get_downdoc_binary_operating_system()}-"
        f"{_get_downdoc_binary_architecture()}"
        f"{_get_downdoc_binary_file_extension()}"
    )

    if not downdoc_binary_filepath.is_file():
        raise FileNotFoundError(downdoc_binary_filepath)

    downdoc_binary_filepath.chmod(downdoc_binary_filepath.stat().st_mode | stat.S_IEXEC)

    return downdoc_binary_filepath
