"""Shared contexts, results, and VAT invoice classes."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any, Mapping

from .money import Money


@dataclass(frozen=True)
class TaxContext:
    """Inputs supplied to a Tax implementation."""

    income: Money = field(default_factory=Money.zero)
    allowances: Money = field(default_factory=Money.zero)
    deductions: Money = field(default_factory=Money.zero)
    resident: bool = True
    on_date: date = date(2026, 7, 1)
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TaxResult:
    """Calculated amount and transparent calculation details."""

    name: str
    amount: Money
    details: Mapping[str, Any] = field(default_factory=dict)


class SupplyTreatment(str, Enum):
    STANDARD = "standard"
    ZERO_RATED = "zero-rated"
    EXEMPT = "exempt"


class InvoiceDirection(str, Enum):
    OUTPUT = "output"
    INPUT = "input"


@dataclass(frozen=True)
class Invoice:
    """A VAT-exclusive invoice amount and its tax treatment."""

    reference: str
    net_amount: Money
    treatment: SupplyTreatment
    direction: InvoiceDirection

