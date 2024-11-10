"""Run Pydowndoc as a module from the CLI with the given arguments."""

from typing import TYPE_CHECKING

import pydowndoc

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__: "Sequence[str]" = ()


if __name__ == "__main__":
    raise SystemExit(pydowndoc.run_with_sys_argv())
