"""Utility functions for pydowndoc."""

import platform
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__: "Sequence[str]" = (
    "get_downdoc_binary_architecture",
    "get_downdoc_binary_file_extension",
    "get_downdoc_binary_operating_system",
)


def get_downdoc_binary_operating_system() -> str:
    """Retriee the string representation of the current operating system."""
    raw_operating_system: str = sys.platform

    if "linux" in raw_operating_system:
        return "linux"

    if "darwin" in raw_operating_system or "macos" in raw_operating_system:
        return "macos"

    if "win" in raw_operating_system and "darwin" not in raw_operating_system:
        return "win"

    raise NotImplementedError(raw_operating_system)


def get_downdoc_binary_architecture() -> str:
    """Retreive the string representation of the current platform architecture."""
    raw_architecture: str = platform.machine()

    if "arm64" in raw_architecture:
        return "arm64"

    if "x86_64" in raw_architecture:
        return "x64"

    raise NotImplementedError(raw_architecture)


def get_downdoc_binary_file_extension() -> str:
    """Retrive the file extension for the executable on the current operating system."""
    raw_operating_system: str = sys.platform

    if "win" in raw_operating_system and "darwin" not in raw_operating_system:
        return ".exe"

    return ""
