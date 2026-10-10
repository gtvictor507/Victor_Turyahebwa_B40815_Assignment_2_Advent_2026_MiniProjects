"""Payroll pipeline composing NSSF, LST, PAYE, and net pay."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .models import TaxContext
from .money import Money
from .taxes import LocalServiceTax, NSSFContribution, PAYE


@dataclass(frozen=True)
class PayrollResult:
    gross_cash_pay: Money
    employee_nssf: Money
    employer_nssf: Money
    local_service_tax: Money
    paye: Money
    net_pay: Money


class PayrollService:
    """Apply the documented assignment pipeline in a fixed, testable order.

    The Order follows: gross salary + cash allowances; calculate NSSF on gross; apply the
    configured LST deduction before PAYE as required by the brief; calculate
    PAYE on the resulting chargeable amount; deduct employee NSSF, LST and
    PAYE from cash pay. Employer NSSF is reported but never taken from net pay.
    """

    def __init__(self, lst: Money = Money.zero()) -> None:
        self.nssf = NSSFContribution()
        self.lst = LocalServiceTax(lst)
        self.paye = PAYE()

    def calculate(
        self,
        salary: Money,
        allowances: Money = Money.zero(),
        *,
        resident: bool = True,
        on_date: date = date(2026, 7, 1),
    ) -> PayrollResult:
        base = TaxContext(income=salary, allowances=allowances, resident=resident, on_date=on_date)
        gross = salary + allowances
        nssf = self.nssf.calculate(base)
        lst = self.lst.calculate(base).amount
        paye = self.paye.calculate(
            TaxContext(income=salary, allowances=allowances, deductions=lst, resident=resident, on_date=on_date)
        ).amount
        net = gross - nssf.amount - lst - paye
        return PayrollResult(
            gross_cash_pay=gross,
            employee_nssf=nssf.amount,
            employer_nssf=nssf.details["employer"],
            local_service_tax=lst,
            paye=paye,
            net_pay=net,
        )

