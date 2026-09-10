import json
import re

from typing import Dict, Any, List, Optional

from services.tavily_service import TavilyService
from services.pexel_service import PexelsService
from services.map_service import MapService


class TravelAgent:
    """
    Travel Agent

    Responsibility:
        1. Receive exactly 3 destinations from ResearchAgent.
        2. Search Tavily for basic destination information.
        3. Retrieve destination image URLs from Pexels.
        4. Retrieve destination coordinates from MapTiler.
        5. Return the information in structured JSON.

    TravelAgent does NOT:
        - select destinations
        - research worker-level travel costs
        - recheck worker results
        - call workers
        - use an LLM
        - calculate budgets
        - create itineraries
        - access databases

    Input:

        {
            "destinations": [
                {
                    "destination": "Tokyo",
                    "country": "Japan"
                },
                {
                    "destination": "Kyoto",
                    "country": "Japan"
                },
                {
                    "destination": "Osaka",
                    "country": "Japan"
                }
            ]
        }

    Output:

        {
            "destinations": [
                {
                    "destination": "Tokyo",
                    "country": "Japan",
                    "basic_info": "...",
                    "images": [
                        "https://..."
                    ],
                    "map_coordinates": {
                        "latitude": 35.6762,
                        "longitude": 139.6503
                    }
                }
            ]
        }
    """

    def __init__(self):

        # =====================================================
        # HELPER SERVICES
        # =====================================================

        self.tavily = TavilyService()
        self.pexels = PexelsService()
        self.map_service = MapService()

    # =========================================================
    # PUBLIC METHOD
    # =========================================================

    def process(
        self,
        research_result: Any
    ) -> Dict[str, Any]:
        """
        Receive the destinations from ResearchAgent and
        enrich each destination with:

            - basic information
            - Pexels images
            - MapTiler coordinates

        The worker results are NOT used here.
        """

        destinations = self._extract_destinations(
            research_result
        )

        self._validate_destinations(
            destinations
        )

        final_results = []

        # -----------------------------------------------------
        # Process each ResearchAgent destination
        # -----------------------------------------------------

        for destination_data in destinations:

            destination = destination_data[
                "destination"
            ]

            country = destination_data[
                "country"
            ]

            # -------------------------------------------------
            # Tavily
            # -------------------------------------------------

            basic_info = self._get_basic_information(
                destination,
                country
            )

            # -------------------------------------------------
            # Pexels
            # -------------------------------------------------

            images = self._get_images(
                destination,
                country
            )

            # -------------------------------------------------
            # MapTiler
            # -------------------------------------------------

            coordinates = self._get_coordinates(
                destination,
                country
            )

            # -------------------------------------------------
            # Final destination object
            # -------------------------------------------------

            final_results.append(
                {
                    "destination": destination,
                    "country": country,
                    "basic_info": basic_info,
                    "images": images,
                    "map_coordinates": coordinates
                }
            )

        return {
            "destinations": final_results
        }

    # =========================================================
    # DESTINATION EXTRACTION
    # =========================================================

    def _extract_destinations(
        self,
        research_result: Any
    ) -> List[Dict[str, str]]:
        """
        Extract destinations from ResearchAgent output.
        """

        if isinstance(
            research_result,
            dict
        ):

            destinations = research_result.get(
                "destinations"
            )

            if destinations is None:

                raise ValueError(
                    "ResearchAgent result is missing "
                    "'destinations'."
                )

            return destinations

        if isinstance(
            research_result,
            list
        ):

            return research_result

        raise TypeError(
            "TravelAgent expected a ResearchAgent "
            "result dictionary or destination list."
        )

    # =========================================================
    # DESTINATION VALIDATION
    # =========================================================

    def _validate_destinations(
        self,
        destinations: List[Dict[str, str]]
    ) -> None:
        """
        Validate the exact three destinations generated
        by ResearchAgent.
        """

        if not isinstance(
            destinations,
            list
        ):

            raise TypeError(
                "destinations must be a list."
            )

        if len(destinations) != 3:

            raise ValueError(
                "TravelAgent requires exactly 3 destinations."
            )

        seen = set()

        for index, destination_data in enumerate(
            destinations,
            start=1
        ):

            if not isinstance(
                destination_data,
                dict
            ):

                raise TypeError(
                    f"Destination {index} must be an object."
                )

            destination = destination_data.get(
                "destination"
            )

            country = destination_data.get(
                "country"
            )

            if not isinstance(
                destination,
                str
            ) or not destination.strip():

                raise ValueError(
                    f"Destination {index} has an invalid name."
                )

            if not isinstance(
                country,
                str
            ) or not country.strip():

                raise ValueError(
                    f"Destination {index} has an invalid country."
                )

            key = self._destination_key(
                destination,
                country
            )

            if key in seen:

                raise ValueError(
                    "ResearchAgent provided duplicate "
                    "destinations."
                )

            seen.add(
                key
            )

    # =========================================================
    # TAVILY
    # =========================================================

    def _get_basic_information(
        self,
        destination: str,
        country: str
    ) -> str:
        """
        Search Tavily for general destination information.

        The output is a single approximately 100-200 word
        paragraph assembled from the returned search content.
        """

        destination_name = (
            f"{destination}, {country}"
        )

        queries = [
            (
                f"{destination_name} travel destination "
                f"overview"
            ),
            (
                f"{destination_name} tourist information "
                f"culture attractions"
            ),
            (
                f"{destination_name} things to know "
                f"for tourists"
            ),
            (
                f"{destination_name} best time to visit "
                f"travel"
            )
        ]

        search_results = self.tavily.search_many(
            queries,
            max_results=5
        )

        text_blocks = []

        for search in search_results:

            results = search.get(
                "results",
                []
            )

            for result in results:

                content = result.get(
                    "content",
                    ""
                )

                if not content:
                    continue

                cleaned = self._clean_text(
                    content
                )

                if cleaned:
                    text_blocks.append(
                        cleaned
                    )

        return self._build_information_paragraph(
            text_blocks
        )

    # =========================================================
    # BUILD BASIC INFORMATION PARAGRAPH
    # =========================================================

    def _build_information_paragraph(
        self,
        text_blocks: List[str]
    ) -> str:
        """
        Build a single 100-200 word paragraph from Tavily
        search results.

        No new factual information is generated here.
        """

        if not text_blocks:

            return (
                "Basic destination information could not "
                "be retrieved from the available web search."
            )

        # -----------------------------------------------------
        # Combine results
        # -----------------------------------------------------

        combined = " ".join(
            text_blocks
        )

        combined = self._clean_text(
            combined
        )

        # -----------------------------------------------------
        # Split into sentences
        # -----------------------------------------------------

        sentences = re.split(
            r"(?<=[.!?])\s+",
            combined
        )

        selected = []
        word_count = 0

        for sentence in sentences:

            sentence = sentence.strip()

            if not sentence:
                continue

            words = sentence.split()

            if not words:
                continue

            # Once we have at least 100 words, stop before
            # going over 200.
            if (
                word_count >= 100
                and word_count + len(words) > 200
            ):
                break

            selected.append(
                sentence
            )

            word_count += len(
                words
            )

            if word_count >= 100:
                break

        # -----------------------------------------------------
        # Fallback
        # -----------------------------------------------------

        if not selected:

            words = combined.split()

            return " ".join(
                words[:200]
            )

        return " ".join(
            selected
        ).strip()

    # =========================================================
    # TEXT CLEANING
    # =========================================================

    def _clean_text(
        self,
        text: str
    ) -> str:
        """
        Clean search-result text.
        """

        if not isinstance(
            text,
            str
        ):
            return ""

        text = text.replace(
            "\n",
            " "
        )

        text = text.replace(
            "\r",
            " "
        )

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text.strip()

    # =========================================================
    # PEXELS
    # =========================================================

    def _get_images(
        self,
        destination: str,
        country: str
    ) -> List[str]:
        """
        Get image URLs from Pexels.
        """

        query = (
            f"{destination}, {country} travel"
        )

        try:

            response = self.pexels.search(
                query
            )

        except Exception as exc:

            print(
                f"Pexels search failed for "
                f"{destination}: {exc}"
            )

            return []

        return self._extract_image_urls(
            response
        )

    # =========================================================
    # IMAGE URL EXTRACTION
    # =========================================================

    def _extract_image_urls(
        self,
        response: Any
    ) -> List[str]:
        """
        Extract image URLs from common Pexels response
        structures.
        """

        if response is None:
            return []

        if isinstance(
            response,
            list
        ):

            return self._extract_urls_from_items(
                response
            )

        if isinstance(
            response,
            dict
        ):

            photos = response.get(
                "photos"
            )

            if isinstance(
                photos,
                list
            ):

                return self._extract_urls_from_items(
                    photos
                )

            images = response.get(
                "images"
            )

            if isinstance(
                images,
                list
            ):

                return self._extract_urls_from_items(
                    images
                )

        return []

    # =========================================================
    # EXTRACT IMAGE URLS
    # =========================================================

    def _extract_urls_from_items(
        self,
        items: List[Any]
    ) -> List[str]:
        """
        Extract usable URLs from Pexels photo objects.
        """

        urls = []

        for item in items:

            # -------------------------------------------------
            # Direct URL
            # -------------------------------------------------

            if isinstance(
                item,
                str
            ):

                if item.startswith(
                    "http"
                ):

                    urls.append(
                        item
                    )

                continue

            if not isinstance(
                item,
                dict
            ):
                continue

            # -------------------------------------------------
            # Pexels photo src
            # -------------------------------------------------

            src = item.get(
                "src"
            )

            if isinstance(
                src,
                dict
            ):

                url = (
                    src.get("large")
                    or src.get("large2x")
                    or src.get("original")
                    or src.get("medium")
                )

                if (
                    isinstance(
                        url,
                        str
                    )
                    and url.startswith("http")
                ):

                    urls.append(
                        url
                    )

                    continue

            # -------------------------------------------------
            # Generic URL
            # -------------------------------------------------

            url = item.get(
                "url"
            )

            if (
                isinstance(
                    url,
                    str
                )
                and url.startswith("http")
            ):

                urls.append(
                    url
                )

        # -----------------------------------------------------
        # Remove duplicates
        # -----------------------------------------------------

        return list(
            dict.fromkeys(
                urls
            )
        )

    # =========================================================
    # MAPTILER
    # =========================================================

    def _get_coordinates(
        self,
        destination: str,
        country: str
    ) -> Optional[Dict[str, float]]:
        """
        Get coordinates through MapService.
        """

        query = (
            f"{destination}, {country}"
        )

        try:

            response = self.map_service.geocode(
                query
            )

        except Exception as exc:

            print(
                f"MapTiler lookup failed for "
                f"{destination}: {exc}"
            )

            return None

        return self._extract_coordinates(
            response
        )

    # =========================================================
    # COORDINATE EXTRACTION
    # =========================================================

    def _extract_coordinates(
        self,
        response: Any
    ) -> Optional[Dict[str, float]]:
        """
        Normalize common MapTiler/MapService responses.
        """

        if response is None:
            return None

        # -----------------------------------------------------
        # Direct latitude/longitude
        # -----------------------------------------------------

        if isinstance(
            response,
            dict
        ):

            if (
                "latitude" in response
                and "longitude" in response
            ):

                try:

                    return {
                        "latitude": float(
                            response["latitude"]
                        ),
                        "longitude": float(
                            response["longitude"]
                        )
                    }

                except (
                    ValueError,
                    TypeError
                ):

                    return None

            # -------------------------------------------------
            # lat/lon
            # -------------------------------------------------

            if (
                "lat" in response
                and "lon" in response
            ):

                try:

                    return {
                        "latitude": float(
                            response["lat"]
                        ),
                        "longitude": float(
                            response["lon"]
                        )
                    }

                except (
                    ValueError,
                    TypeError
                ):

                    return None

            # -------------------------------------------------
            # GeoJSON geometry
            # -------------------------------------------------

            geometry = response.get(
                "geometry"
            )

            coordinates = self._coordinates_from_geometry(
                geometry
            )

            if coordinates:
                return coordinates

            # -------------------------------------------------
            # MapTiler feature collection
            # -------------------------------------------------

            features = response.get(
                "features"
            )

            if (
                isinstance(
                    features,
                    list
                )
                and features
            ):

                first_feature = features[0]

                if isinstance(
                    first_feature,
                    dict
                ):

                    coordinates = (
                        self._coordinates_from_geometry(
                            first_feature.get(
                                "geometry"
                            )
                        )
                    )

                    if coordinates:
                        return coordinates

        # -----------------------------------------------------
        # Raw coordinate list
        #
        # GeoJSON order:
        # [longitude, latitude]
        # -----------------------------------------------------

        if isinstance(
            response,
            list
        ):

            if len(response) >= 2:

                try:

                    return {
                        "latitude": float(
                            response[1]
                        ),
                        "longitude": float(
                            response[0]
                        )
                    }

                except (
                    ValueError,
                    TypeError
                ):

                    return None

        return None

    # =========================================================
    # GEOMETRY COORDINATES
    # =========================================================

    def _coordinates_from_geometry(
        self,
        geometry: Any
    ) -> Optional[Dict[str, float]]:
        """
        Extract coordinates from a GeoJSON geometry object.
        """

        if not isinstance(
            geometry,
            dict
        ):
            return None

        coordinates = geometry.get(
            "coordinates"
        )

        if (
            not isinstance(
                coordinates,
                list
            )
            or len(coordinates) < 2
        ):

            return None

        try:

            return {
                "latitude": float(
                    coordinates[1]
                ),
                "longitude": float(
                    coordinates[0]
                )
            }

        except (
            ValueError,
            TypeError
        ):

            return None

    # =========================================================
    # DESTINATION KEY
    # =========================================================

    def _destination_key(
        self,
        destination: str,
        country: str
    ) -> str:
        """
        Create a normalized destination identifier.
        """

        return (
            f"{destination.strip().lower()}|"
            f"{country.strip().lower()}"
        )

    # =========================================================
    # SAVE JSON
    # =========================================================

    def save_json(
        self,
        result: Dict[str, Any],
        file_path: str = "travel_results.json"
    ) -> str:
        """
        Save TravelAgent's output as JSON.
        """

        with open(
            file_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                result,
                file,
                indent=4,
                ensure_ascii=False
            )

        return file_path