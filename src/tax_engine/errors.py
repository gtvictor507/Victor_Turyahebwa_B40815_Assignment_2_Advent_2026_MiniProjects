"""Expected error handling for the tax engine."""

class TaxError(Exception):
    """Base class for tax-engine errors."""

class InvalidIncomeError(TaxError):
    """Raised for a negative or otherwise invalid monetary input."""

class NoScheduleForDateError(TaxError):
    """Raised when the engine has no law/rate schedule for a requested date."""