"""Boundary and property-based tests for the Uganda tax engine."""

from datetime import date
from decimal import Decimal

from hypothesis import given, strategies as st
import pytest

from src.tax_engine import (
    CorporateIncomeTax,
    Invoice,
    InvoiceDirection,
    Money,
    PAYE,
    PayrollService,
    SupplyTreatment,
    TaxContext,
    VAT,
)


EFFECTIVE = date(2026, 7, 1)


@pytest.mark.parametrize(
    ("income", "expected"),
    [
        (335_000, 0),
        (335_001, 0),  # 20 cents rounds to a whole UGX using ROUND_HALF_UP
        (410_000, 15_000),
        (485_000, 33_750),
        (10_000_000, 2_888_250),
        (10_000_001, 2_888_250),  # 40 cents rounds down to a whole UGX
    ],
)
def test_resident_paye_boundaries(income: int, expected: int) -> None:
    result = PAYE().calculate(TaxContext(income=Money(income), on_date=EFFECTIVE))
    assert result.amount == Money(expected)


@pytest.mark.parametrize(
    ("income", "expected"),
    [(0, 0), (335_000, 33_500), (410_000, 48_500), (10_000_000, 2_925_500)],
)
def test_non_resident_paye_boundaries(income: int, expected: int) -> None:
    result = PAYE().calculate(
        TaxContext(income=Money(income), resident=False, on_date=EFFECTIVE)
    )
    assert result.amount == Money(expected)


def test_payroll_does_not_deduct_employer_nssf_from_net_pay() -> None:
    result = PayrollService(lst=Money(10_000)).calculate(Money(1_000_000))
    assert result.employee_nssf == Money(50_000)
    assert result.employer_nssf == Money(100_000)
    assert result.net_pay == result.gross_cash_pay - result.employee_nssf - result.local_service_tax - result.paye


def test_vat_standard_zero_and_exempt_supplies() -> None:
    invoices = [
        Invoice("S1", Money(1_000_000), SupplyTreatment.STANDARD, InvoiceDirection.OUTPUT),
        Invoice("Z1", Money(500_000), SupplyTreatment.ZERO_RATED, InvoiceDirection.OUTPUT),
        Invoice("E1", Money(200_000), SupplyTreatment.EXEMPT, InvoiceDirection.OUTPUT),
        Invoice("P1", Money(400_000), SupplyTreatment.STANDARD, InvoiceDirection.INPUT),
    ]
    result = VAT().calculate(TaxContext(metadata={"invoices": invoices}))
    assert result.details["output_vat"] == Money(180_000)
    assert result.details["input_vat"] == Money(72_000)
    assert result.amount == Money(108_000)


def test_corporate_income_tax_uses_chargeable_income() -> None:
    result = CorporateIncomeTax().calculate(
        TaxContext(income=Money(100_000_000), deductions=Money(40_000_000))
    )
    assert result.amount == Money(18_000_000)


income_strategy = st.integers(min_value=0, max_value=100_000_000)


@given(income_strategy)
def test_paye_is_non_negative_and_never_exceeds_income(income: int) -> None:
    tax = PAYE().calculate(TaxContext(income=Money(income), on_date=EFFECTIVE)).amount
    assert Money.zero() <= tax <= Money(income)


@given(income_strategy, income_strategy)
def test_paye_is_monotonic(left: int, right: int) -> None:
    lower, upper = sorted((left, right))
    lower_tax = PAYE().calculate(TaxContext(income=Money(lower), on_date=EFFECTIVE)).amount
    upper_tax = PAYE().calculate(TaxContext(income=Money(upper), on_date=EFFECTIVE)).amount
    assert lower_tax <= upper_tax


def test_float_is_rejected_by_money() -> None:
    with pytest.raises(TypeError):
        Money(0.1)

