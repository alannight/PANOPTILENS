"""Provider boundary and privacy-conscious reverse geocoding implementation."""

import abc
import json
import logging
import math
import time
from threading import Lock
from typing import Any, Callable
from urllib.parse import urlencode
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)


class GeocodingProvider(abc.ABC):
    """Interface implemented by online and offline reverse geocoders."""

    @abc.abstractmethod
    def reverse_geocode(self, latitude: float, longitude: float) -> dict[str, str | None] | None:
        """Return a structured address, or None when no result is available."""


class NominatimProvider(GeocodingProvider):
    """Nominatim implementation with rounded-coordinate caching and timeouts."""

    def __init__(
        self,
        timeout: float = 3.0,
        min_delay: float = 1.0,
        cache_precision: int = 4,
        requester: Callable[[str, float, dict[str, str]], dict[str, Any]] | None = None,
    ) -> None:
        self.timeout = timeout
        self.min_delay = min_delay
        self.cache_precision = cache_precision
        self._requester = requester or self._request_json
        self._cache: dict[tuple[float, float], dict[str, str | None]] = {}
        self._last_request_time = 0.0
        self._lock = Lock()

    @staticmethod
    def _request_json(url: str, timeout: float, headers: dict[str, str]) -> dict[str, Any]:
        request = Request(url, headers=headers)
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def reverse_geocode(self, latitude: float, longitude: float) -> dict[str, str | None] | None:
        try:
            latitude, longitude = float(latitude), float(longitude)
            if not (math.isfinite(latitude) and math.isfinite(longitude)):
                return None
            if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                return None
        except (TypeError, ValueError, OverflowError):
            return None

        rounded_latitude = round(latitude, self.cache_precision)
        rounded_longitude = round(longitude, self.cache_precision)
        cache_key = rounded_latitude, rounded_longitude
        with self._lock:
            if cache_key in self._cache:
                return self._cache[cache_key]

            elapsed = time.monotonic() - self._last_request_time
            if elapsed < self.min_delay:
                time.sleep(self.min_delay - elapsed)
            self._last_request_time = time.monotonic()

            parameters = urlencode({
                "format": "jsonv2",
                "lat": rounded_latitude,
                "lon": rounded_longitude,
                "zoom": 18,
                "addressdetails": 1,
            })
            headers = {"User-Agent": "PANOPTILENS/1.0 (digital forensics metadata service)"}
            try:
                data = self._requester(
                    f"https://nominatim.openstreetmap.org/reverse?{parameters}",
                    self.timeout,
                    headers,
                )
                address = data.get("address")
                if not isinstance(address, dict):
                    return None
                result = {
                    "country": address.get("country"),
                    "province": address.get("state") or address.get("province"),
                    "city": address.get("city") or address.get("town") or address.get("village"),
                    "district": address.get("suburb") or address.get("city_district") or address.get("county"),
                    "road": address.get("road"),
                    "formatted": data.get("display_name"),
                }
                self._cache[cache_key] = result
                return result
            except Exception as exc:
                logger.warning("reverse geocoding unavailable (error_type=%s)", type(exc).__name__)
                return None


default_geocoder = NominatimProvider()