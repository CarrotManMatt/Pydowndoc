"""Common utility classes internal to this project."""

__all__: "Sequence[str]" = ("OUTPUT_CONVERSION_TO_STRING", "ConversionError")

import sys
from typing import TYPE_CHECKING

if sys.version_info >= (3, 12):
    pass
else:
    pass

if sys.version_info < (3, 15):  # noqa: CAR105
    from typing_extensions import sentinel

if TYPE_CHECKING:
    from collections.abc import Sequence


OUTPUT_CONVERSION_TO_STRING = sentinel("OUTPUT_CONVERSION_TO_STRING")


class ConversionError(RuntimeError):
    """Raised when an error occurs while using the downdoc binary in a subprocess."""

    def __init__(
        self,
        message: str | None = None,
        *,
        subprocess_return_code: int | None = None,
        subprocess_stderr: str | None = None,
    ) -> None:
        self.message: str | None = message
        self.subprocess_return_code: int | None = subprocess_return_code
        self.subprocess_stderr: str | None = subprocess_stderr
