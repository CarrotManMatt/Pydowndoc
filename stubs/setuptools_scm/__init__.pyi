from collections.abc import Sequence
from pathlib import Path

from .version import ScmVersion

__all__: Sequence[str] = ("get_version",)

def get_version(
    *,
    root: Path = ...,
    version_scheme: str | ScmVersion = ...,
    local_scheme: str | ScmVersion = ...,
) -> str: ...
