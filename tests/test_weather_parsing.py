"""Offline tests: no API traffic is generated."""

from pathlib import Path

import pytest

from src.weather_api import (
    ForecastError,
    choose_location,
    first_met_observation,
    forecast_to_dataframe,
    load_json,
    validate_coordinates,
    weather_description,
)


DATA = Path(__file__).resolve().parents[1] / "data"


def test_missing_geocoding_results_is_handled() -> None:
    payload = load_json(DATA / "geocoding_empty.json")
    assert payload.get("results", []) == []


def test_ambiguous_candidate_can_be_selected_by_index() -> None:
    candidates = load_json(DATA / "geocoding_kampala.json")["results"]
    assert choose_location(candidates, 1)["admin1"] == "Western Region"


def test_weather_code_decoding() -> None:
    assert weather_description(95) == "Thunderstorm"
    assert weather_description(777).startswith("Unknown code")


def test_forecast_dataframe_has_units_and_rows() -> None:
    frame = forecast_to_dataframe(load_json(DATA / "open_meteo_forecast.json"))
    assert len(frame) == 7
    assert "Maximum temperature (°C)" in frame.columns
    assert frame.iloc[0]["Weather"] == "Slight rain"


def test_invalid_latitude_is_rejected() -> None:
    with pytest.raises(ForecastError, match="Latitude"):
        validate_coordinates(91, 32.5)


def test_met_fixture_extracts_first_point() -> None:
    point = first_met_observation(load_json(DATA / "met_norway_forecast.json"))
    assert point["air_temperature_c"] == 25.8
    assert point["wind_speed_m_s"] == 3.6

