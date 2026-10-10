"""An immutable UGX money value object."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any


UGX_QUANTUM = Decimal("1")


def _decimal(value: Decimal | int | str) -> Decimal:
    if isinstance(value, float):
        raise TypeError("float is not accepted for money; use Decimal, int, or str")
    return value if isinstance(value, Decimal) else Decimal(str(value))


@dataclass(frozen=True)
class Money:
    """Whole-shilling UGX amount rounded half up after each operation."""

    amount: Decimal
    currency: str = "UGX"

    def __init__(self, amount: Decimal | int | str = 0, currency: str = "UGX") -> None:
        if currency != "UGX":
            raise ValueError("This assignment's Money object supports UGX only.")
        object.__setattr__(self, "amount", _decimal(amount).quantize(UGX_QUANTUM, rounding=ROUND_HALF_UP))
        object.__setattr__(self, "currency", currency)

    def _check(self, other: Any) -> "Money":
        if not isinstance(other, Money) or other.currency != self.currency:
            raise TypeError("Money operations require matching Money currencies.")
        return other

    def __add__(self, other: Any) -> "Money":
        checked = self._check(other)
        return Money(self.amount + checked.amount, self.currency)

    def __sub__(self, other: Any) -> "Money":
        checked = self._check(other)
        return Money(self.amount - checked.amount, self.currency)

    def __mul__(self, factor: Decimal | int | str) -> "Money":
        return Money(self.amount * _decimal(factor), self.currency)

    def __rmul__(self, factor: Decimal | int | str) -> "Money":
        return self * factor

    def __lt__(self, other: Any) -> bool:
        return self.amount < self._check(other).amount

    def __le__(self, other: Any) -> bool:
        return self.amount <= self._check(other).amount

    def __repr__(self) -> str:
        return f"Money(UGX {self.amount:,.0f})"

    def __str__(self) -> str:
        return f"UGX {self.amount:,.0f}"

    @classmethod
    def zero(cls) -> "Money":
        return cls(0)


def maximum(left: Money, right: Money) -> Money:
    """Return the larger Money value without converting to float."""

    return right if left < right else left

