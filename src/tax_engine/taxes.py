"""Uganda tax and contribution implementations for the extension task."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from typing import Iterable

from .errors import InvalidIncomeError, NoScheduleForDateError, TaxError
from .models import Invoice, InvoiceDirection, SupplyTreatment, TaxContext, TaxResult
from .money import Money, maximum


ZERO = Money.zero()


class Tax(ABC):
    """Abstraction used here."""

    @abstractmethod
    def calculate(self, ctx: TaxContext) -> TaxResult:
        """Calculate a tax or statutory amount from *ctx*."""


def _non_negative(name: str, value: Money) -> None:
    if value < ZERO:
        raise InvalidIncomeError(f"{name} cannot be negative: {value}")


class PAYE(Tax):
    """Monthly PAYE using the URA latest schedule effective 1 July 2026."""

    EFFECTIVE_FROM = date(2026, 7, 1)

    def calculate(self, ctx: TaxContext) -> TaxResult:
        if ctx.on_date < self.EFFECTIVE_FROM:
            raise NoScheduleForDateError(
                f"No PAYE schedule configured before {self.EFFECTIVE_FROM.isoformat()}."
            )
        _non_negative("income", ctx.income)
        _non_negative("allowances", ctx.allowances)
        _non_negative("deductions", ctx.deductions)
        chargeable = maximum(ctx.income + ctx.allowances - ctx.deductions, ZERO)
        tax = self._resident(chargeable) if ctx.resident else self._non_resident(chargeable)
        return TaxResult(
            "PAYE",
            tax,
            {
                "chargeable_income": chargeable,
                "residency": "resident" if ctx.resident else "non-resident",
                "schedule_effective_from": self.EFFECTIVE_FROM.isoformat(),
            },
        )

    @staticmethod
    def _resident(income: Money) -> Money:
        x = income.amount
        if x <= Decimal("335000"):
            return ZERO
        if x <= Decimal("410000"):
            return Money((x - Decimal("335000")) * Decimal("0.20"))
        if x <= Decimal("485000"):
            return Money(Decimal("15000") + (x - Decimal("410000")) * Decimal("0.25"))
        base = Decimal("33750") + (x - Decimal("485000")) * Decimal("0.30")
        if x > Decimal("10000000"):
            base += (x - Decimal("10000000")) * Decimal("0.10")
        return Money(base)

    @staticmethod
    def _non_resident(income: Money) -> Money:
        x = income.amount
        if x <= Decimal("335000"):
            return Money(x * Decimal("0.10"))
        if x <= Decimal("410000"):
            return Money(Decimal("33500") + (x - Decimal("335000")) * Decimal("0.20"))
        base = Decimal("48500") + (x - Decimal("410000")) * Decimal("0.30")
        if x > Decimal("10000000"):
            base += (x - Decimal("10000000")) * Decimal("0.10")
        return Money(base)


class NSSFContribution(Tax):
    """Employee 5% and employer 10% contributions on gross monthly wage."""

    EMPLOYEE_RATE = Decimal("0.05")
    EMPLOYER_RATE = Decimal("0.10")

    def calculate(self, ctx: TaxContext) -> TaxResult:
        gross = ctx.income + ctx.allowances
        _non_negative("gross wage", gross)
        employee = gross * self.EMPLOYEE_RATE
        employer = gross * self.EMPLOYER_RATE
        return TaxResult(
            "NSSF employee contribution",
            employee,
            {"employee": employee, "employer": employer, "total_remittance": employee + employer},
        )


class LocalServiceTax(Tax):
    """Configurable payroll deduction supplied by the caller."""

    def __init__(self, monthly_amount: Money = ZERO) -> None:
        _non_negative("Local Service Tax", monthly_amount)
        self.monthly_amount = monthly_amount

    def calculate(self, ctx: TaxContext) -> TaxResult:
        gross = ctx.income + ctx.allowances
        amount = self.monthly_amount if self.monthly_amount <= gross else gross
        return TaxResult("Local Service Tax", amount, {"configured_amount": self.monthly_amount})


class VAT(Tax):
    """VAT ledger for standard-rated, zero-rated, and exempt invoices."""

    RATE = Decimal("0.18")

    def calculate(self, ctx: TaxContext) -> TaxResult:
        invoices = ctx.metadata.get("invoices", [])
        if not isinstance(invoices, Iterable):
            raise TaxError("metadata['invoices'] must be an iterable of Invoice objects")
        output_vat = ZERO
        input_vat = ZERO
        for invoice in invoices:
            if not isinstance(invoice, Invoice):
                raise TaxError("Every VAT item must be an Invoice")
            _non_negative(f"invoice {invoice.reference}", invoice.net_amount)
            vat = invoice.net_amount * self.RATE if invoice.treatment is SupplyTreatment.STANDARD else ZERO
            if invoice.direction is InvoiceDirection.OUTPUT:
                output_vat = output_vat + vat
            else:
                input_vat = input_vat + vat
        balance = output_vat - input_vat
        payable = maximum(balance, ZERO)
        credit = maximum(Money(-balance.amount), ZERO)
        return TaxResult(
            "Net VAT payable",
            payable,
            {"output_vat": output_vat, "input_vat": input_vat, "credit_carried_forward": credit},
        )


class CorporateIncomeTax(Tax):
    """Resident-company income tax at 30% of chargeable income."""

    RATE = Decimal("0.30")

    def calculate(self, ctx: TaxContext) -> TaxResult:
        _non_negative("revenue", ctx.income)
        _non_negative("allowable deductions", ctx.deductions)
        chargeable = maximum(ctx.income - ctx.deductions, ZERO)
        tax = chargeable * self.RATE
        return TaxResult(
            "Corporate income tax",
            tax,
            {"revenue": ctx.income, "allowable_deductions": ctx.deductions, "chargeable_income": chargeable},
        )

