"""Project build script to package binary artefacts into platform-specific builds."""

import platform
import re
import sys
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import TYPE_CHECKING, override

import tomllib
from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from hatchling.builders.wheel import WheelBuilder, WheelBuilderConfig

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Literal, Protocol

    from hatchling.builders.config import BuilderConfig
    from hatchling.builders.plugin.interface import BuilderInterface
    from hatchling.plugin.manager import PluginManager

__all__: "Sequence[str]" = (
    "MultiArtefactWheelBuilder",
    "get_builder",
    "print_downdoc_executables",
)


type BuildHookConfig = Mapping[Literal["operating-systems", "architectures"], Iterable[str]]


if TYPE_CHECKING:

    class _ProtocolBuildFunc(Protocol):
        def __call__(self, directory: str, **build_data: object) -> str: ...


def _get_artefact_targets(config: "Mapping[str, object]") -> BuildHookConfig:
    operating_systems: object | Iterable[str] = config.get("operating-systems", [sys.platform])
    if not isinstance(operating_systems, Iterable):
        raise TypeError

    architectures: object | Iterable[str] = config.get("architectures", [platform.machine()])
    if not isinstance(architectures, Iterable):
        raise TypeError

    return {"architectures": architectures, "operating-systems": operating_systems}


def _print_downdoc_executables(config: "Mapping[str, object]") -> None:
    artefact_targets: BuildHookConfig = _get_artefact_targets(config)
    sys.stdout.write(
        re.sub(
            ",,+",
            ",",
            ",".join(
                (
                    f"{
                    "linux-"
                    if "linux" in operating_system
                    else "macos-"
                    if "macos" in operating_system or "darwin" in operating_system
                    else "win-"
                    if "win" in operating_system and "darwin" not in operating_system
                    else ""
                }"
                    f"{
                    "x64"
                    if "x86_64" in architecture
                    else "arm64"
                    if "arm64" in architecture
                    else ""
                }"
                )
                for operating_system in artefact_targets["operating-systems"]
                for architecture in artefact_targets["architectures"]
            ),
        ).strip(",")
    )
    sys.stdout.write("\n")


def print_downdoc_executables() -> None:
    """Output the total set of pydowndoc binary file names for every OS & architecture."""
    tool_dict: object | None = tomllib.loads(
        (Path(__file__).parent / "pyproject.toml").read_text()
    ).get("tool", None)

    if tool_dict is None:
        _print_downdoc_executables({})
        return

    if not isinstance(tool_dict, Mapping):
        raise TypeError

    hatch_dict: object | None = tool_dict.get("hatch", None)

    if hatch_dict is None:
        _print_downdoc_executables({})
        return

    if not isinstance(hatch_dict, Mapping):
        raise TypeError

    build_dict: object | None = hatch_dict.get("build", None)

    if build_dict is None:
        _print_downdoc_executables({})
        return

    if not isinstance(build_dict, Mapping):
        raise TypeError

    targets_dict: object | None = build_dict.get("targets", None)

    if targets_dict is None:
        _print_downdoc_executables({})
        return

    if not isinstance(targets_dict, Mapping):
        raise TypeError

    custom_dict: object | None = targets_dict.get("custom", None)

    if custom_dict is None:
        _print_downdoc_executables({})
        return

    if not isinstance(custom_dict, Mapping):
        raise TypeError

    _print_downdoc_executables(custom_dict)


class MultiArtefactWheelBuilder(WheelBuilder):
    """Build multiple wheels at once with each set of binary executables."""

    class _BuildHook(BuildHookInterface[WheelBuilderConfig]):
        @override
        def initialize(self, version: str, build_data: dict[str, object]) -> None:
            downdoc_binary_filepath: Path = Path(self.root) / (
                "downloads/downdoc-"
                f"{
                    "linux-"
                    if "linux" in version
                    else "macos-"
                    if "macos" in version or "darwin" in version
                    else "win-"
                    if "win" in version and "darwin" not in version
                    else ""
                }"
                f"{"x64" if "x86_64" in version else "arm64" if "arm64" in version else ""}"
                f"{".exe" if "win" in version and "darwin" not in version else ""}"
            )

            if not downdoc_binary_filepath.is_file():
                raise FileNotFoundError(downdoc_binary_filepath)

            force_include: object | Mapping[str, str] = build_data.get("force_include", {})
            if not isinstance(force_include, Mapping):
                raise TypeError

            build_data["force_include"] = {
                str(downdoc_binary_filepath.resolve()): "pydowndoc/downdoc-binary",
                **force_include,
            }
            build_data["other"] = build_data.get("force_include", {})

            build_data["tag"] = f"py3-none-{version}"

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
            "force_include_editable": {},
            "extra_metadata": {},
            "shared_data": {},
            "shared_scripts": {},
        }

    @override
    def get_default_tag(self) -> str:
        raise NotImplementedError

    @override
    def get_best_matching_tag(self) -> str:
        raise NotImplementedError

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
    def get_default_versions(self) -> list[str]:
        return list(self.get_version_api())

    @override
    def get_version_api(self) -> dict[str, "_ProtocolBuildFunc"]:
        artefact_targets: BuildHookConfig = _get_artefact_targets(self.target_config)

        return {
            f"{operating_system}_{architecture}": self.build_standard
            for operating_system in artefact_targets["operating-systems"]
            for architecture in artefact_targets["architectures"]
        }

    @override
    def build_standard(self, directory: str, **build_data: object) -> str:
        build_data["infer_tag"] = False
        build_data["pure_python"] = False
        return super().build_standard(directory, **build_data)


def get_builder() -> (
    "type[BuilderInterface[BuilderConfig, PluginManager]] | "
    "Iterable[type[BuilderInterface[BuilderConfig, PluginManager]]]"
):
    """Retrieve the correct hatch builder hook class."""
    return MultiArtefactWheelBuilder
