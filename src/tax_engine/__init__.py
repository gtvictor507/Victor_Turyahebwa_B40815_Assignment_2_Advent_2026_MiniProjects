"""Extensible Uganda tax engine used by Mini-Project 2.
This __init__.py file tells Python that a directory should be treated as a Python package.
"""

from .errors import (
    InvalidIncomeError,
    NoScheduleForDateError,
    TaxError,
)

from .models import (
    Invoice,
    InvoiceDirection,
    SupplyTreatment,
    TaxContext,
    TaxResult,
)

from .money import Money
from .payroll import PayrollResult, PayrollService
from .planner import TaxPlanner

from .taxes import (
    CorporateIncomeTax,
    LocalServiceTax,
    NSSFContribution,
    PAYE,
    Tax,
    VAT,
)

__all__ = [
    "CorporateIncomeTax",
    "InvalidIncomeError",
    "Invoice",
    "InvoiceDirection",
    "LocalServiceTax",
    "Money",
    "NoScheduleForDateError",
    "NSSFContribution",
    "PAYE",
    "PayrollResult",
    "PayrollService",
    "SupplyTreatment",
    "Tax",
    "TaxContext",
    "TaxError",
    "TaxPlanner",
    "TaxResult",
    "VAT",
]