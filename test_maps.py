import json

from location.map import MapService


def print_section(title):
    """Print a formatted test section."""

    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def validate_location(location):
    """
    Validate the basic structure returned by MapService.
    """

    required_fields = [
        "query",
        "found",
        "name",
        "place_id",
        "longitude",
        "latitude",
        "country",
        "region",
        "place_type",
        "categories"
    ]

    for field in required_fields:

        if field not in location:

            raise AssertionError(
                f"Missing required field: {field}"
            )

    if not location["found"]:

        raise AssertionError(
            "Location was not found."
        )

    if location["latitude"] is None:

        raise AssertionError(
            "Latitude is missing."
        )

    if location["longitude"] is None:

        raise AssertionError(
            "Longitude is missing."
        )

    # ----------------------------------------------------------
    # Validate coordinate ranges.
    # ----------------------------------------------------------

    latitude = location["latitude"]
    longitude = location["longitude"]

    if not -90 <= latitude <= 90:

        raise AssertionError(
            f"Invalid latitude: {latitude}"
        )

    if not -180 <= longitude <= 180:

        raise AssertionError(
            f"Invalid longitude: {longitude}"
        )

    return True


def test_map_service_initialization():
    """
    Test 1:
    Verify that MapService can initialize correctly.
    """

    print_section(
        "TEST 1 — MAP SERVICE INITIALIZATION"
    )

    print(
        "\nInitializing MapService..."
    )

    maps = MapService()

    print(
        "MapService initialized successfully."
    )

    print(
        f"API base URL: {maps.base_url}"
    )

    print(
        "✓ MapService initialization passed."
    )

    return maps


def test_geocode(maps):
    """
    Test 2:
    Test MapTiler forward geocoding.
    """

    print_section(
        "TEST 2 — FORWARD GEOCODING"
    )

    location_name = (
        "Zurich, Switzerland"
    )

    print(
        f"\nSearching for:\n{location_name}"
    )

    result = maps.geocode(
        location_name,
        limit=3
    )

    print(
        "\nRaw MapTiler response:"
    )

    print(
        json.dumps(
            result,
            indent=4
        )
    )

    # ----------------------------------------------------------
    # Validate GeoJSON response.
    # ----------------------------------------------------------

    if "features" not in result:

        raise AssertionError(
            "MapTiler response does not contain "
            "'features'."
        )

    if not isinstance(
        result["features"],
        list
    ):

        raise AssertionError(
            "'features' must be a list."
        )

    if not result["features"]:

        raise AssertionError(
            "MapTiler returned no matching locations."
        )

    print(
        f"\nFound {len(result['features'])} "
        "location result(s)."
    )

    print(
        "✓ Forward geocoding passed."
    )

    return result


def test_get_location(maps):
    """
    Test 3:
    Test the simplified location structure.
    """

    print_section(
        "TEST 3 — LOCATION INFORMATION"
    )

    location_name = (
        "Zurich, Switzerland"
    )

    print(
        f"\nGetting location information for:\n"
        f"{location_name}"
    )

    location = maps.get_location(
        location_name
    )

    print(
        "\nSimplified location:"
    )

    print(
        json.dumps(
            location,
            indent=4
        )
    )

    validate_location(
        location
    )

    print(
        "\n✓ Location structure passed."
    )

    return location


def test_coordinates(maps):
    """
    Test 4:
    Verify that MapTiler returns usable global coordinates.

    These coordinates will eventually be useful for:

        - 2D maps
        - 3D globe
        - route visualization
        - destination markers
        - map animations
    """

    print_section(
        "TEST 4 — GLOBAL COORDINATES"
    )

    destinations = [
        "Vancouver, Canada",
        "Tokyo, Japan",
        "Zurich, Switzerland"
    ]

    print(
        "\nTesting destinations:"
    )

    for destination in destinations:

        print(
            f"• {destination}"
        )

    results = maps.get_locations(
        destinations
    )

    if len(results) != len(
        destinations
    ):

        raise AssertionError(
            "Number of returned locations does not "
            "match number of requested locations."
        )

    print(
        "\nCoordinates:"
    )

    for result in results:

        validate_location(
            result
        )

        print(
            f"\n{result['name']}"
        )

        print(
            f"  Latitude:  {result['latitude']}"
        )

        print(
            f"  Longitude: {result['longitude']}"
        )

        print(
            f"  Country:   {result['country']}"
        )

    print(
        "\n✓ Global coordinate test passed."
    )

    return results


def test_reverse_geocoding(maps):
    """
    Test 5:
    Test reverse geocoding.

    Coordinates are converted back into location
    information.
    """

    print_section(
        "TEST 5 — REVERSE GEOCODING"
    )

    # Approximate Zurich coordinates.

    longitude = 8.5417
    latitude = 47.3769

    print(
        "\nCoordinates:"
    )

    print(
        f"Longitude: {longitude}"
    )

    print(
        f"Latitude:  {latitude}"
    )

    result = maps.reverse_geocode(
        longitude=longitude,
        latitude=latitude
    )

    print(
        "\nMapTiler reverse-geocoding response:"
    )

    print(
        json.dumps(
            result,
            indent=4
        )
    )

    if "features" not in result:

        raise AssertionError(
            "Reverse geocoding response does not "
            "contain 'features'."
        )

    print(
        "\n✓ Reverse geocoding passed."
    )

    return result


def test_destination_info(maps):
    """
    Test 6:
    Test the combined destination information method.
    """

    print_section(
        "TEST 6 — DESTINATION INFORMATION"
    )

    destination = (
        "Vancouver, Canada"
    )

    print(
        f"\nGetting destination information for:\n"
        f"{destination}"
    )

    result = maps.get_destination_info(
        destination
    )

    print(
        "\nDestination information:"
    )

    print(
        json.dumps(
            result,
            indent=4
        )
    )

    # ----------------------------------------------------------
    # Validate structure.
    # ----------------------------------------------------------

    required_fields = [
        "destination",
        "location",
        "map"
    ]

    for field in required_fields:

        if field not in result:

            raise AssertionError(
                f"Missing field: {field}"
            )

    location = result["location"]

    validate_location(
        location
    )

    map_data = result["map"]

    if "latitude" not in map_data:

        raise AssertionError(
            "Map data is missing latitude."
        )

    if "longitude" not in map_data:

        raise AssertionError(
            "Map data is missing longitude."
        )

    if "provider" not in map_data:

        raise AssertionError(
            "Map data is missing provider."
        )

    if map_data["provider"] != "MapTiler":

        raise AssertionError(
            "Map provider is not MapTiler."
        )

    print(
        "\n✓ Destination information test passed."
    )

    return result


def test_map_config(maps):
    """
    Test 7:
    Verify that the MapTiler frontend configuration
    can be generated.
    """

    print_section(
        "TEST 7 — MAP CONFIGURATION"
    )

    result = maps.get_map_config()

    print(
        "\nMap configuration:"
    )

    # Do not print the complete API key.

    safe_result = dict(
        result
    )

    if safe_result.get(
        "api_key"
    ):

        safe_result["api_key"] = (
            "********"
        )

    print(
        json.dumps(
            safe_result,
            indent=4
        )
    )

    # ----------------------------------------------------------
    # Validate structure.
    # ----------------------------------------------------------

    required_fields = [
        "provider",
        "style",
        "api_key",
        "map_style"
    ]

    for field in required_fields:

        if field not in result:

            raise AssertionError(
                f"Missing map configuration field: "
                f"{field}"
            )

    if result["provider"] != "MapTiler":

        raise AssertionError(
            "Map provider is not MapTiler."
        )

    if not result["style"]:

        raise AssertionError(
            "Map style URL is empty."
        )

    print(
        "\n✓ Map configuration test passed."
    )

    return result


def main():

    print("=" * 60)
    print("MAPTILER MAP SERVICE TEST")
    print("=" * 60)

    print(
        "\nTesting:"
    )

    print(
        "  • MapService initialization"
    )

    print(
        "  • MapTiler forward geocoding"
    )

    print(
        "  • Location information"
    )

    print(
        "  • Global coordinates"
    )

    print(
        "  • Reverse geocoding"
    )

    print(
        "  • Destination information"
    )

    print(
        "  • Map configuration"
    )

    try:

        # ======================================================
        # TEST 1
        # ======================================================

        maps = test_map_service_initialization()

        # ======================================================
        # TEST 2
        # ======================================================

        test_geocode(
            maps
        )

        # ======================================================
        # TEST 3
        # ======================================================

        test_get_location(
            maps
        )

        # ======================================================
        # TEST 4
        # ======================================================

        test_coordinates(
            maps
        )

        # ======================================================
        # TEST 5
        # ======================================================

        test_reverse_geocoding(
            maps
        )

        # ======================================================
        # TEST 6
        # ======================================================

        test_destination_info(
            maps
        )

        # ======================================================
        # TEST 7
        # ======================================================

        test_map_config(
            maps
        )

        # ======================================================
        # ALL TESTS PASSED
        # ======================================================

        print_section(
            "ALL MAP TESTS PASSED"
        )

        print(
            "\nMapTiler is successfully connected "
            "to the project."
        )

        print(
            "\nThe MapService can currently provide:"
        )

        print(
            "  ✓ Location searches"
        )

        print(
            "  ✓ Geographic coordinates"
        )

        print(
            "  ✓ Place IDs"
        )

        print(
            "  ✓ Country / region information"
        )

        print(
            "  ✓ Reverse geocoding"
        )

        print(
            "  ✓ Map configuration"
        )

        print(
            "\nThe service is ready to be connected "
            "to main.py."
        )

    except Exception as error:

        print_section(
            "MAP TEST FAILED"
        )

        print(
            f"\nError: {error}"
        )

        print(
            "\nCheck the following:"
        )

        print(
            "1. MAPTILER_API_KEY exists in .env"
        )

        print(
            "2. The MapTiler API key is valid."
        )

        print(
            "3. Internet access is available."
        )

        print(
            "4. The MapTiler API is accessible."
        )

        print(
            "5. requests and python-dotenv are installed."
        )

        return


if __name__ == "__main__":
    main()