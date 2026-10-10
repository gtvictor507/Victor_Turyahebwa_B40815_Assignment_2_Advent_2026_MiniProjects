"""Extension B: compare two payroll scenarios."""

from __future__ import annotations

from dataclasses import asdict
from datetime import date
from typing import Any

from .money import Money
from .payroll import PayrollService


class TaxPlanner:
    """Compare alternative salary/allowance structures without giving tax advice."""

    def __init__(self, payroll: PayrollService) -> None:
        self.payroll = payroll

    def compare(
        self,
        scenario_a: tuple[Money, Money],
        scenario_b: tuple[Money, Money],
        *,
        resident: bool = True,
        on_date: date = date(2026, 7, 1),
    ) -> dict[str, Any]:
        first = self.payroll.calculate(*scenario_a, resident=resident, on_date=on_date)
        second = self.payroll.calculate(*scenario_b, resident=resident, on_date=on_date)
        return {
            "scenario_a": asdict(first),
            "scenario_b": asdict(second),
            "net_pay_difference_b_minus_a": second.net_pay - first.net_pay,
        }

