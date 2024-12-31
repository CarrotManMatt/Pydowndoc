"""Utility classes & funtions used throughout the Pydowndoc project."""

from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from typing import Final


__all__: "Sequence[str]" = ("classproperty",)


T_value = TypeVar("T_value")


class classproperty(property, Generic[T_value]):
    """
    Decorator for a Class-level property.

    Vendored from https://github.com/CarrotManMatt/typed_classproperties

    Credit to Denis Rhyzhkov on Stackoverflow: https://stackoverflow.com/a/13624858/1280629
    """

    def __init__(self, func: "Callable[..., T_value]", /) -> None:  # type: ignore[misc]
        """Initialise the classproperty object."""
        super().__init__(func)

    def __get__(self, owner_self: object, owner_cls: "type | None" = None, /) -> T_value:
        """Retrieve the value of the property."""
        if self.fget is None:
            BROKEN_OBJECT_MESSAGE: Final[str] = "Broken object 'classproperty'."
            raise RuntimeError(BROKEN_OBJECT_MESSAGE)

        value: T_value = self.fget(owner_cls)
        return value
