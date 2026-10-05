from app.services.geocoding import GeocodingProvider, NominatimProvider


class MockGeocoder(GeocodingProvider):
    def reverse_geocode(self, latitude: float, longitude: float):
        return {"country": "Testland", "formatted": f"{latitude},{longitude}"}


def test_geocoding_provider_is_replaceable_by_mock():
    provider = MockGeocoder()

    assert isinstance(provider, GeocodingProvider)
    assert provider.reverse_geocode(1.0, 2.0)["country"] == "Testland"


def test_nominatim_maps_and_caches_structured_address():
    requests = []

    def requester(url, timeout, headers):
        requests.append((url, timeout, headers))
        return {
            "display_name": "Main Street, Sample City, Testland",
            "address": {
                "country": "Testland",
                "state": "Sample Province",
                "city": "Sample City",
                "suburb": "Sample District",
                "road": "Main Street",
            },
        }

    provider = NominatimProvider(min_delay=0, requester=requester)
    expected = {
        "country": "Testland",
        "province": "Sample Province",
        "city": "Sample City",
        "district": "Sample District",
        "road": "Main Street",
        "formatted": "Main Street, Sample City, Testland",
    }

    assert provider.reverse_geocode(1.23451, 2.34561) == expected
    assert provider.reverse_geocode(1.23452, 2.34562) == expected
    assert len(requests) == 1
    assert requests[0][1] == 3.0
    assert requests[0][2]["User-Agent"].startswith("PANOPTILENS/")


def test_nominatim_failure_returns_none_without_raising():
    def timeout(*_):
        raise TimeoutError()

    provider = NominatimProvider(min_delay=0, requester=timeout)

    assert provider.reverse_geocode(1.0, 2.0) is None
    assert provider.reverse_geocode(91.0, 2.0) is None