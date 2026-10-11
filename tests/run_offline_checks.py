"""Dependency-light smoke checks for environments where pytest is not installed.

Run from the repository root with: ``python tests/run_offline_checks.py``.
The formal assessment suite remains the pytest/Hypothesis files.
"""

from datetime import date
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.tax_engine import Money, PAYE, TaxContext  # noqa: E402
from src.weather_api import (  # noqa: E402
    first_met_observation,
    forecast_to_dataframe,
    load_json,
    weather_description,
)


def main() -> None:
    data = ROOT / "data"
    forecast = forecast_to_dataframe(load_json(data / "open_meteo_forecast.json"))
    assert len(forecast) == 7
    assert weather_description(95) == "Thunderstorm"
    assert first_met_observation(load_json(data / "met_norway_forecast.json"))["wind_speed_m_s"] == 3.6

    paye = PAYE()
    effective = date(2026, 7, 1)
    expected = {
        335_000: 0,
        335_001: 0,
        410_000: 15_000,
        485_000: 33_750,
        10_000_000: 2_888_250,
        10_000_001: 2_888_250,
    }
    for income, tax in expected.items():
        result = paye.calculate(TaxContext(income=Money(income), on_date=effective))
        assert result.amount == Money(tax)

    previous = Money.zero()
    for income in range(0, 20_000_001, 10_000):
        tax = paye.calculate(TaxContext(income=Money(income), on_date=effective)).amount
        assert Money.zero() <= tax <= Money(income)
        assert previous <= tax
        previous = tax
    print("Offline weather, boundary, boundedness, and monotonicity checks passed.")


if __name__ == "__main__":
    main()

