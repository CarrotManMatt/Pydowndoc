""""""

from typing import TYPE_CHECKING

from pydowndoc import console

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__: "Sequence[str]" = ()


if __name__ == "__main__":
    raise SystemExit(console.run())
