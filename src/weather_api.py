"""
Weather Forecast api for weather Mini-Project 1
This module calls Open-Meteo and MET Norway directly. 
Network access is isolated from parsing so saved JSON fixtures can
be used for offline, deterministic tests.
"""

from __future__ import annotations #the line tells Python to save type hints for later instead of interpreting them immediately.
from dataclasses import dataclass
import json
from pathlib import Path
import time
from typing import Any, Callable, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import pandas as pd

try:  # This lets the parsing tests run even before optional dependencies are installed.
    import requests
except ImportError:
    requests = None

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
MET_NORWAY_URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact"

WMO_WEATHER_CODES: dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


class WeatherAPIError(RuntimeError):
    """Base exception for a weather-service failure."""

class GeocodingError(WeatherAPIError):
    """Raised when a place cannot be geocoded."""

class ForecastError(WeatherAPIError):
    """Raised when forecast retrieval or parsing fails."""

@dataclass(frozen=True) #create the standard class methods (__init__, __repr__, etc.) and prevent objects of this class from being modified after creation.
class RequestMetadata:
    """Observable HTTP information required by Part A."""

    status_code: int
    content_type: str
    elapsed_seconds: float
    url: str


def load_json(path: str | Path) -> dict[str, Any]:
    """
    Function receives either a file-path string or a Path object and 
    returns a dictionary whose keys are strings and whose values may be of any type.
    """
    """Load a UTF-8 JSON fixture."""

    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def _candidates(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return a list of dictionaries; a missing results key means no match."""

    results = payload.get("results", [])
    return [dict(item) for item in results if isinstance(item, Mapping)]


def geocode_urllib(name: str, timeout: float = 10.0) -> tuple[list[dict[str, Any]], RequestMetadata]:
    """Geocode *name* using only urllib, urllib.parse, and json."""

    if not name.strip():
        raise GeocodingError("Location name cannot be blank.")
    query = urlencode({"name": name.strip(), "count": 10, "language": "en", "format": "json"})
    url = f"{GEOCODING_URL}?{query}"
    request = Request(url, headers={"Accept": "application/json"})
    started = time.perf_counter()
    try:
        with urlopen(request, timeout=timeout) as response:  # nosec B310 - fixed HTTPS endpoint
            raw = response.read()
            payload = json.loads(raw.decode(response.headers.get_content_charset() or "utf-8"))
            metadata = RequestMetadata(
                status_code=response.status,
                content_type=response.headers.get("Content-Type", ""),
                elapsed_seconds=time.perf_counter() - started,
                url=response.geturl(),
            )
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise GeocodingError(f"urllib geocoding failed for {name!r}: {exc}") from exc
    return _candidates(payload), metadata


def request_json(
    url: str,
    *,
    params: Mapping[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
    timeout: float = 10.0,
    retries: int = 3,
    backoff: float = 0.5,
    session: Any | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> tuple[dict[str, Any], RequestMetadata]:
    """GET JSON with timeout, status checking, bounded retries, and backoff.

    Connection failures, timeouts, HTTP 429, and 5xx responses are retryable.
    Other 4xx responses fail immediately. A :class:`WeatherAPIError` is raised
    after the final failed attempt.
    """

    if requests is None:
        raise WeatherAPIError("The 'requests' package is required. Run: pip install -r requirements.txt")
    if timeout <= 0 or retries < 0 or backoff < 0:
        raise ValueError("timeout must be positive; retries and backoff must be non-negative")

    client = session or requests.Session()
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        started = time.perf_counter()
        try:
            response = client.get(url, params=params, headers=dict(headers or {}), timeout=timeout)
            if response.status_code == 429 or response.status_code >= 500:
                response.raise_for_status()
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError("Expected a JSON object")
            return payload, RequestMetadata(
                status_code=response.status_code,
                content_type=response.headers.get("Content-Type", ""),
                elapsed_seconds=time.perf_counter() - started,
                url=response.url,
            )
        except Exception as exc:  # normalised to one domain exception below
            last_error = exc
            status = getattr(getattr(exc, "response", None), "status_code", None)
            retryable = status is None or status == 429 or (isinstance(status, int) and status >= 500)
            if attempt >= retries or not retryable:
                break
            sleep(backoff * (2**attempt))
    raise WeatherAPIError(f"Request failed after {retries + 1} attempt(s): {last_error}") from last_error


def geocode_requests(name: str, timeout: float = 10.0) -> tuple[list[dict[str, Any]], RequestMetadata]:
    """Geocode *name* with requests and its ``params`` argument."""

    if not name.strip():
        raise GeocodingError("Location name cannot be blank.")
    try:
        payload, metadata = request_json(
            GEOCODING_URL,
            params={"name": name.strip(), "count": 10, "language": "en", "format": "json"},
            timeout=timeout,
        )
    except WeatherAPIError as exc:
        raise GeocodingError(str(exc)) from exc
    return _candidates(payload), metadata


def geocode(name: str, timeout: float = 10.0) -> list[dict[str, Any]]:
    """Return geocoding candidates, including an empty list for no result."""

    candidates, _ = geocode_requests(name, timeout=timeout)
    return candidates


def format_candidates(candidates: Sequence[Mapping[str, Any]]) -> list[str]:
    """Create numbered labels that expose ambiguity to the user."""

    labels: list[str] = []
    for index, item in enumerate(candidates):
        parts = [item.get("name"), item.get("admin1"), item.get("country")]
        labels.append(f"{index}: {', '.join(str(p) for p in parts if p)}")
    return labels


def choose_location(candidates: Sequence[Mapping[str, Any]], index: int = 0) -> dict[str, Any]:
    """Select one explicitly indexed candidate and validate its coordinates."""

    if not candidates:
        raise GeocodingError("No matching locations were returned.")
    if index < 0 or index >= len(candidates):
        raise GeocodingError(f"Candidate index {index} is outside 0..{len(candidates) - 1}.")
    selected = dict(candidates[index])
    validate_coordinates(selected.get("latitude"), selected.get("longitude"))
    return selected


def validate_coordinates(latitude: Any, longitude: Any) -> tuple[float, float]:
    """Validate and return latitude/longitude as floats."""

    try:
        lat, lon = float(latitude), float(longitude)
    except (TypeError, ValueError) as exc:
        raise ForecastError("Latitude and longitude must be numeric.") from exc
    if not -90 <= lat <= 90:
        raise ForecastError("Latitude must be between -90 and 90 degrees.")
    if not -180 <= lon <= 180:
        raise ForecastError("Longitude must be between -180 and 180 degrees.")
    return lat, lon


def get_forecast(lat: float, lon: float, days: int = 7, timeout: float = 10.0) -> dict[str, Any]:
    """Retrieve a daily Open-Meteo forecast with location-matched dates."""

    latitude, longitude = validate_coordinates(lat, lon)
    if not 1 <= days <= 16:
        raise ForecastError("Forecast days must be between 1 and 16.")
    try:
        payload, _ = request_json(
            FORECAST_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
                "timezone": "auto",
                "forecast_days": days,
            },
            timeout=timeout,
        )
    except WeatherAPIError as exc:
        raise ForecastError(str(exc)) from exc
    return payload


def weather_description(code: int) -> str:
    """Decode an Open-Meteo WMO weather code."""

    return WMO_WEATHER_CODES.get(int(code), f"Unknown code ({code})")


def forecast_to_dataframe(payload: Mapping[str, Any]) -> pd.DataFrame:
    """Convert Open-Meteo daily JSON to a labelled DataFrame with unit-bearing columns."""

    daily = payload.get("daily")
    if not isinstance(daily, Mapping):
        raise ForecastError("Forecast JSON has no 'daily' object.")
    required = [
        "time",
        "weather_code",
        "temperature_2m_max",
        "temperature_2m_min",
        "precipitation_sum",
        "wind_speed_10m_max",
    ]
    missing = [key for key in required if key not in daily]
    if missing:
        raise ForecastError(f"Forecast JSON is missing: {', '.join(missing)}")
    lengths = {len(daily[key]) for key in required}
    if len(lengths) != 1:
        raise ForecastError("Daily forecast arrays have inconsistent lengths.")

    units = payload.get("daily_units", {})
    frame = pd.DataFrame(
        {
            "Date": pd.to_datetime(daily["time"]),
            "Weather": [weather_description(code) for code in daily["weather_code"]],
            f"Maximum temperature ({units.get('temperature_2m_max', '°C')})": daily["temperature_2m_max"],
            f"Minimum temperature ({units.get('temperature_2m_min', '°C')})": daily["temperature_2m_min"],
            f"Precipitation ({units.get('precipitation_sum', 'mm')})": daily["precipitation_sum"],
            f"Maximum wind speed ({units.get('wind_speed_10m_max', 'km/h')})": daily["wind_speed_10m_max"],
        }
    )
    return frame


def met_norway_forecast(
    lat: float,
    lon: float,
    contact_email: str,
    timeout: float = 10.0,
) -> dict[str, Any]:
    """Retrieve MET Norway Locationforecast 2.0 using an identifying User-Agent."""

    latitude, longitude = validate_coordinates(lat, lon)
    if "@" not in contact_email or "example" in contact_email.lower():
        raise ForecastError("Please enter your real university email.")
    payload, _ = request_json(
        MET_NORWAY_URL,
        params={"lat": round(latitude, 4), "lon": round(longitude, 4)},
        headers={"User-Agent": f"UCU-Weather-MiniProject/1.0 {contact_email}"},
        timeout=timeout,
    )
    return payload


def first_met_observation(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Extract the first instant from a MET Norway compact response."""

    try:
        point = payload["properties"]["timeseries"][0]
        details = point["data"]["instant"]["details"]
        return {
            "time": point["time"],
            "air_temperature_c": details["air_temperature"],
            "wind_speed_m_s": details["wind_speed"],
        }
    except (KeyError, IndexError, TypeError) as exc:
        raise ForecastError("MET Norway response has an unexpected structure.") from exc

