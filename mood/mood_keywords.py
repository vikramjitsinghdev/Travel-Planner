# mood_keywords.py

import re


class MoodKeywords:
    """
    Stores the travel mood vocabulary and provides methods for:

    1. Accessing mood categories
    2. Searching keywords
    3. Traversing the keyword library
    4. Detecting keywords inside sentences
    5. Detecting whether a matched keyword is wanted/rejected
    6. Validating a sentence
    """

    def __init__(self):

        self.mood_keywords = {

            # ==================================================
            # NATURE
            # ==================================================
            "nature": [
                "nature",
                "natural",
                "natural beauty",
                "natural scenery",
                "natural landscape",
                "landscape",
                "landscapes",
                "scenery",
                "scenic",
                "outdoors",
                "outdoor",
                "wilderness",
                "countryside",
                "rural",
                "greenery",
                "forests",
                "forest",
                "woods",
                "woodlands",
                "valleys",
                "valley",
                "lakes",
                "lake",
                "rivers",
                "river",
                "waterfalls",
                "waterfall",
                "canyons",
                "canyon",
                "cliffs",
                "cliff",
                "national parks",
                "national park",
                "nature reserve",
                "nature reserves",
                "untouched nature",
                "pristine nature",
            ],

            # ==================================================
            # ADVENTURE
            # ==================================================
            "adventure": [
                "adventure",
                "adventurous",
                "exciting",
                "excitement",
                "thrill",
                "thrilling",
                "adrenaline",
                "extreme",
                "explore",
                "exploring",
                "exploration",
                "expedition",
                "expeditions",
                "action",
                "action-packed",
                "action packed",
                "extreme activities",
                "extreme sports",
                "adventure activities",
                "adventure travel",
                "off-road",
                "off road",
            ],

            # ==================================================
            # RELAXATION
            # ==================================================
            "relaxation": [
                "relax",
                "relaxed",
                "relaxing",
                "rest",
                "restful",
                "unwind",
                "unwinding",
                "peace",
                "peaceful",
                "calm",
                "calming",
                "tranquil",
                "tranquility",
                "serene",
                "serenity",
                "rejuvenating",
                "slow-paced",
                "slow paced",
                "laid-back",
                "laid back",
                "stress-free",
                "stress free",
                "wellness",
                "spa",
                "retreat",
                "meditation",
                "mindfulness",
                "peace and quiet",
            ],

            # ==================================================
            # COMFORT
            # ==================================================
            "comfort": [
                "comfort",
                "comfortable",
                "comforting",
                "cozy",
                "cosy",
                "convenient",
                "convenience",
                "pleasant",
                "welcoming",
                "hassle-free",
                "hassle free",
                "easy travel",
                "easy trip",
                "comfortable stay",
                "good accommodation",
                "nice accommodation",
                "comfortable accommodation",
            ],

            # ==================================================
            # CULTURE
            # ==================================================
            "culture": [
                "culture",
                "cultural",
                "cultural experience",
                "local culture",
                "tradition",
                "traditions",
                "traditional",
                "local traditions",
                "local life",
                "local lifestyle",
                "authentic",
                "authenticity",
                "local people",
                "festivals",
                "heritage",
                "arts",
                "artistic",
            ],

            # ==================================================
            # HISTORY
            # ==================================================
            "history": [
                "history",
                "historical",
                "historic",
                "ancient",
                "ancient history",
                "ancient ruins",
                "ruins",
                "archaeology",
                "archaeological",
                "historical sites",
                "historic sites",
                "historical places",
                "historic places",
                "historical landmarks",
                "historic landmarks",
                "battlefields",
                "fortresses",
                "history tour",
                "historical tour",
            ],

            # ==================================================
            # FOOD
            # ==================================================
            "food": [
                "food",
                "cuisine",
                "culinary",
                "dining",
                "restaurant",
                "restaurants",
                "foodie",
                "foodies",
                "gastronomy",
                "local food",
                "local cuisine",
                "street food",
                "food tasting",
                "food tour",
                "food market",
                "local dishes",
                "traditional food",
                "fine dining",
                "cafes",
                "cafe",
                "bakery",
                "bakeries",
            ],

            # ==================================================
            # NIGHTLIFE
            # ==================================================
            "nightlife": [
                "nightlife",
                "night life",
                "party",
                "partying",
                "clubs",
                "club",
                "nightclub",
                "nightclubs",
                "night club",
                "night clubs",
                "bars",
                "bar",
                "pubs",
                "pub",
                "drinking",
                "late night",
                "late-night",
                "social scene",
                "dancing",
                "dj",
                "bar hopping",
                "party scene",
                "club scene",
            ],

            # ==================================================
            # LUXURY
            # ==================================================
            "luxury": [
                "luxury",
                "luxurious",
                "premium",
                "high-end",
                "high end",
                "upscale",
                "five-star",
                "five star",
                "exclusive",
                "lavish",
                "indulgent",
                "pampering",
                "first-class",
                "first class",
                "business class",
                "private villa",
                "private resort",
            ],

            # ==================================================
            # ROMANCE
            # ==================================================
            "romance": [
                "romance",
                "romantic",
                "romantic getaway",
                "romantic vacation",
                "couple",
                "couples",
                "honeymoon",
                "anniversary",
                "intimate",
                "couples retreat",
                "romantic dinner",
                "romantic hotel",
                "romantic resort",
                "date night",
            ],

            # ==================================================
            # FAMILY
            # ==================================================
            "family": [
                "family",
                "families",
                "family trip",
                "family vacation",
                "family holiday",
                "family-friendly",
                "family friendly",
                "kid-friendly",
                "kid friendly",
                "child-friendly",
                "child friendly",
                "children",
                "kids",
                "family activities",
                "family attractions",
                "family resort",
                "family accommodation",
            ],

            # ==================================================
            # SOLO
            # ==================================================
            "solo": [
                "solo",
                "solo travel",
                "solo trip",
                "solo vacation",
                "solo holiday",
                "travel alone",
                "traveling alone",
                "travelling alone",
                "alone",
                "on my own",
                "by myself",
                "independent travel",
                "independent traveler",
                "independent traveller",
                "solo traveler",
                "solo traveller",
                "explore alone",
            ],

            # ==================================================
            # PHOTOGRAPHY
            # ==================================================
            "photography": [
                "photography",
                "photographer",
                "photo",
                "photos",
                "pictures",
                "photogenic",
                "instagrammable",
                "instagramable",
                "instagram-worthy",
                "instagram worthy",
                "photo opportunities",
                "photo spots",
                "photography spots",
                "scenic photos",
                "beautiful photos",
                "sunrise photography",
                "sunset photography",
                "landscape photography",
                "wildlife photography",
                "travel photography",
                "architecture photography",
            ],

            # ==================================================
            # BEACHES
            # ==================================================
            "beaches": [
                "beach",
                "beaches",
                "beach vacation",
                "beach holiday",
                "beach trip",
                "seaside",
                "sea side",
                "seashore",
                "shore",
                "shoreline",
                "coast",
                "coastline",
                "coastal",
                "coastal vacation",
                "coastal trip",
                "tropical beach",
                "tropical beaches",
                "white sand",
                "sandy beach",
                "oceanfront",
                "ocean front",
                "beach resort",
                "seaside resort",
            ],

            # ==================================================
            # MOUNTAINS
            # ==================================================
            "mountains": [
                "mountain",
                "mountains",
                "mountainous",
                "mountain trip",
                "mountain vacation",
                "mountain getaway",
                "mountain views",
                "mountain scenery",
                "mountain landscape",
                "alpine",
                "alps",
                "rockies",
                "rocky mountains",
                "highlands",
                "peaks",
                "summits",
                "mountain villages",
                "mountain town",
                "hills",
                "rolling hills",
            ],

            # ==================================================
            # SNOW
            # ==================================================
            "snow": [
                "snow",
                "snowy",
                "snowfall",
                "ski",
                "skiing",
                "snowboarding",
                "winter sports",
                "winter activities",
                "winter wonderland",
                "snowy mountains",
                "snow-covered",
                "snow covered",
                "ice skating",
                "frozen lakes",
                "winter vacation",
                "winter holiday",
                "winter trip",
                "snow resort",
                "ski resort",
            ],

            # ==================================================
            # HIKING
            # ==================================================
            "hiking": [
                "hiking",
                "hike",
                "hikes",
                "hiker",
                "hikers",
                "trek",
                "trekking",
                "trail",
                "trails",
                "walking trails",
                "hiking trails",
                "mountain hiking",
                "day hike",
                "long hike",
                "multi-day hike",
                "backpacking",
                "nature walks",
                "footpath",
                "footpaths",
                "trekking route",
            ],

            # ==================================================
            # WATER SPORTS
            # ==================================================
            "water_sports": [
                "water sports",
                "watersports",
                "water activities",
                "swimming",
                "swim",
                "surfing",
                "surf",
                "kayaking",
                "kayak",
                "canoeing",
                "canoe",
                "rafting",
                "whitewater rafting",
                "paddleboarding",
                "paddle board",
                "jet skiing",
                "jet ski",
                "parasailing",
                "diving",
                "scuba diving",
                "scuba",
                "snorkeling",
                "snorkelling",
                "snorkel",
                "sailing",
                "windsurfing",
                "water skiing",
                "wakeboarding",
                "fishing",
            ],

            # ==================================================
            # SHOPPING
            # ==================================================
            "shopping": [
                "shopping",
                "shop",
                "shops",
                "shopper",
                "shoppers",
                "shopping district",
                "shopping mall",
                "mall",
                "malls",
                "market",
                "markets",
                "street markets",
                "local markets",
                "souvenirs",
                "souvenir shopping",
                "boutiques",
                "boutique",
                "designer stores",
                "designer shopping",
                "fashion",
                "fashion district",
                "outlets",
                "local crafts",
                "craft markets",
            ],

            # ==================================================
            # ARCHITECTURE
            # ==================================================
            "architecture": [
                "architecture",
                "architectural",
                "building",
                "buildings",
                "design",
                "urban design",
                "historic architecture",
                "modern architecture",
                "modern buildings",
                "traditional architecture",
                "ancient architecture",
                "gothic architecture",
                "baroque architecture",
                "contemporary architecture",
                "skyscraper",
                "skyscrapers",
                "landmark",
                "landmarks",
                "monument",
                "monuments",
                "palace",
                "palaces",
                "castle",
                "castles",
                "temple",
                "temples",
                "shrine",
                "shrines",
                "church",
                "churches",
                "mosque",
                "mosques",
                "cathedral",
                "cathedrals",
            ],

            # ==================================================
            # MUSEUMS
            # ==================================================
            "museums": [
                "museum",
                "museums",
                "art museum",
                "history museum",
                "science museum",
                "gallery",
                "galleries",
                "art gallery",
                "art galleries",
                "exhibition",
                "exhibitions",
                "exhibit",
                "exhibits",
                "cultural museum",
                "museum tour",
                "museum tours",
                "museum hopping",
                "historical museum",
            ],

            # ==================================================
            # WILDLIFE
            # ==================================================
            "wildlife": [
                "wildlife",
                "wild animals",
                "animals",
                "animal watching",
                "animal spotting",
                "wildlife watching",
                "wildlife viewing",
                "safari",
                "safaris",
                "bird watching",
                "birdwatching",
                "whale watching",
                "whales",
                "dolphin watching",
                "dolphins",
                "marine life",
                "sea life",
                "nature reserve",
                "wildlife reserve",
            ],

            # ==================================================
            # SPIRITUALITY
            # ==================================================
            "spirituality": [
                "spirituality",
                "spiritual",
                "spiritual trip",
                "spiritual travel",
                "spiritual retreat",
                "religion",
                "religious",
                "religious sites",
                "pilgrimage",
                "pilgrimages",
                "temple visit",
                "monastery",
                "monasteries",
                "sacred sites",
                "sacred places",
                "mindfulness",
                "inner peace",
                "reflection",
            ],

            # ==================================================
            # ROAD TRIPS
            # ==================================================
            "road_trips": [
                "road trip",
                "road trips",
                "roadtrip",
                "roadtrips",
                "driving trip",
                "driving trips",
                "drive",
                "driving",
                "self-drive",
                "self drive",
                "rental car",
                "rent a car",
                "car trip",
                "car trips",
                "scenic drive",
                "scenic drives",
                "road journey",
                "road journeys",
                "long drive",
                "cross-country drive",
                "cross country drive",
            ],

            # ==================================================
            # REMOTE
            # ==================================================
            "remote": [
                "remote",
                "remote place",
                "remote places",
                "remote destination",
                "remote destinations",
                "secluded",
                "seclusion",
                "isolated",
                "isolation",
                "off-grid",
                "off grid",
                "off the grid",
                "off-the-beaten-path",
                "off the beaten path",
                "hidden gem",
                "hidden gems",
                "undiscovered",
                "less touristy",
                "away from tourists",
                "away from crowds",
                "wilderness getaway",
            ],

            # ==================================================
            # URBAN
            # ==================================================
            "urban": [
                "urban",
                "urban area",
                "urban life",
                "urban environment",
                "urban setting",

                "modern",
                "modern city",
                "modern cities",
                "modern architecture",
                "modern lifestyle",

                "city",
                "cities",
                "big city",
                "big cities",
                "major city",
                "major cities",
                "large city",
                "large cities",
                "city center",
                "city centre",
                "downtown",
                "city life",
                "city break",
                "city trip",
                "city vacation",

                "metropolitan",
                "metropolitan area",
                "metropolitan city",
                "metropolis",
                "cosmopolitan",

                "contemporary city",
                "contemporary cities",
            ],

            # ==================================================
            # CROWDED
            # ==================================================
            "crowded": [
                "crowded",
                "crowd",
                "crowds",
                "busy",
                "busy city",
                "busy streets",
                "bustling",
                "bustling city",
                "bustling streets",
                "packed",
                "packed streets",
                "lots of people",
                "lots of tourists",
                "many tourists",
                "large crowds",
                "heavy crowds",
                "high foot traffic",
                "touristy",
                "tourist-heavy",
                "tourist heavy",
                "tourist hotspot",
                "tourist hotspots",
                "very popular",
                "popular destination",
                "popular destinations",
                "lively",
                "vibrant",
            ],

            # ==================================================
            # QUIET
            # ==================================================
            "quiet": [
                "quiet",
                "quiet place",
                "quiet places",
                "quiet destination",
                "quiet destinations",
                "peaceful",
                "peace",
                "peace and quiet",
                "peaceful getaway",
                "peaceful vacation",
                "peaceful trip",
                "peaceful environment",
                "peaceful surroundings",
                "calm",
                "calming",
                "calm destination",
                "calm environment",
                "calm atmosphere",
                "tranquil",
                "tranquility",
                "serene",
                "serenity",
                "uncrowded",
                "not crowded",
                "few people",
                "fewer people",
                "low-key",
                "low key",
                "laid-back",
                "laid back",
                "silent",
                "silence",
                "secluded",
            ],

            # ==================================================
            # WARM WEATHER
            # ==================================================
            "warm_weather": [
                "warm",
                "warm weather",
                "warm climate",
                "warm temperatures",
                "hot",
                "hot weather",
                "hot climate",
                "hot temperatures",
                "sunny",
                "sunny weather",
                "sunny climate",
                "sunshine",
                "tropical",
                "tropical weather",
                "tropical climate",
                "tropical destination",
                "summer weather",
                "summer climate",
            ],

            # ==================================================
            # COLD WEATHER
            # ==================================================
            "cold_weather": [
                "cold",
                "cold weather",
                "cold climate",
                "cold temperatures",
                "cool",
                "cool weather",
                "cool climate",
                "cool temperatures",
                "chilly",
                "freezing",
                "frozen",
                "icy",
                "winter",
                "winter weather",
                "winter climate",
                "winter destination",
                "snowy weather",
            ],
        }

        self.negation_phrases = [
            "do not want",
            "don't want",
            "does not want",
            "doesn't want",
            "did not want",
            "didn't want",

            "do not like",
            "don't like",
            "does not like",
            "doesn't like",
            "did not like",
            "didn't like",

            "not interested in",
            "not interested",
            "not looking for",
            "not looking to",

            "no interest in",
            "not a fan of",

            "avoid",
            "avoiding",
            "without",
            "exclude",
            "excluding",
            "excluded",

            "stay away from",
            "stay away",

            "hate",
            "hates",
            "dislike",
            "dislikes",
        ]

    # ==========================================================
    # NORMALIZATION
    # ==========================================================

    def normalize(self, text: str) -> str:
        """
        Converts text into a consistent searchable format.
        """

        text = text.lower().strip()

        # Treat hyphens as spaces.
        text = text.replace("-", " ")

        # Remove repeated whitespace.
        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text

    # ==========================================================
    # GET ALL MOOD CATEGORIES
    # ==========================================================

    def get_moods(self):
        """
        Returns every canonical mood category.
        """

        return list(
            self.mood_keywords.keys()
        )

    # ==========================================================
    # GET KEYWORDS FOR ONE MOOD
    # ==========================================================

    def get_keywords(self, mood: str):
        """
        Returns every keyword belonging to a mood.
        """

        mood = self.normalize(mood)

        return self.mood_keywords.get(
            mood,
            []
        )

    # ==========================================================
    # TRANSVERSE ENTIRE KEYWORD LIBRARY
    # ==========================================================

    def traverse_keywords(self):
        """
        Generator that goes through every mood and every keyword.

        Example:

            for mood, keyword in finder.traverse_keywords():
                print(mood, keyword)
        """

        for mood, keywords in self.mood_keywords.items():

            for keyword in keywords:

                yield mood, keyword

    # ==========================================================
    # SEARCH KEYWORD IN SENTENCE
    # ==========================================================

    def search_keyword(
        self,
        sentence: str,
        keyword: str,
    ) -> bool:
        """
        Returns True if the keyword exists in the sentence.

        Handles:
        - capitalization
        - hyphen/space differences
        - whole-word matching
        - basic plural forms
        """

        sentence = self.normalize(sentence)
        keyword = self.normalize(keyword)

        pattern = (
            rf"(?<!\w)"
            rf"{re.escape(keyword)}"
            rf"(?!\w)"
        )

        if re.search(
            pattern,
            sentence,
        ):
            return True

        # Basic plural support.
        if keyword.endswith("y"):

            plural = (
                keyword[:-1]
                + "ies"
            )

        else:

            plural = (
                keyword
                + "s"
            )

        plural_pattern = (
            rf"(?<!\w)"
            rf"{re.escape(plural)}"
            rf"(?!\w)"
        )

        return bool(
            re.search(
                plural_pattern,
                sentence,
            )
        )

    # ==========================================================
    # FIND MOOD FROM SENTENCE
    # ==========================================================

    def find_mood(
        self,
        sentence: str,
    ):
        """
        Searches the sentence against the entire mood library.

        Returns a list of canonical mood categories that were
        found.

        Example:

            "I want a peaceful modern city."

        returns:

            ["urban", "quiet"]
        """

        found_moods = []

        for mood, keywords in (
            self.mood_keywords.items()
        ):

            for keyword in keywords:

                if self.search_keyword(
                    sentence,
                    keyword,
                ):

                    if mood not in found_moods:

                        found_moods.append(
                            mood
                        )

                    break

        return found_moods

    # ==========================================================
    # FIND THE ACTUAL KEYWORDS
    # ==========================================================

    def find_keywords(
        self,
        sentence: str,
    ):
        """
        Returns the actual keywords found rather than just
        the canonical mood category.

        Example:

            "I want a peaceful modern city."

        might return:

            {
                "urban": ["modern", "city"],
                "quiet": ["peaceful"]
            }
        """

        found = {}

        for mood, keywords in (
            self.mood_keywords.items()
        ):

            matches = []

            for keyword in keywords:

                if self.search_keyword(
                    sentence,
                    keyword,
                ):

                    matches.append(
                        keyword
                    )

            if matches:

                found[mood] = matches

        return found

    # ==========================================================
    # CHECK WHETHER KEYWORD IS NEGATED
    # ==========================================================

    def is_negated(
        self,
        sentence: str,
        keyword: str,
    ) -> bool:
        """
        Returns:

            True  -> keyword is being rejected
            False -> keyword is being requested

        Example:

            "I want mountains."

                -> False

            "I don't want mountains."

                -> True
        """

        sentence = self.normalize(sentence)
        keyword = self.normalize(keyword)

        position = sentence.find(
            keyword
        )

        if position == -1:

            return False

        before_keyword = (
            sentence[:position]
        )

        # Check explicit negative phrases.
        for phrase in self.negation_phrases:

            if phrase in before_keyword:

                return True

        # Short-range negation.
        words = before_keyword.split()

        recent_words = words[-5:]

        if any(
            word in {
                "not",
                "no",
                "never",
            }
            for word in recent_words
        ):

            return True

        return False

    # ==========================================================
    # VALIDATE ONE KEYWORD
    # ==========================================================

    def validate_keyword(
        self,
        sentence: str,
        mood: str,
        keyword: str,
    ) -> bool:
        """
        Validates whether a particular keyword is positively
        expressed in the sentence.

        Returns:

            True  -> wanted
            False -> rejected OR not found
        """

        if not self.search_keyword(
            sentence,
            keyword,
        ):

            return False

        if self.is_negated(
            sentence,
            keyword,
        ):

            return False

        return True

    # ==========================================================
    # VALIDATE SENTENCE
    # ==========================================================

    def validate_sentence(
        self,
        sentence: str,
    ) -> bool:
        """
        Returns True if the sentence contains at least one
        recognized POSITIVE travel preference.

        Returns False if:
        - no known mood keyword exists
        - all recognized keywords are negated
        """

        found_keywords = (
            self.find_keywords(sentence)
        )

        if not found_keywords:

            return False

        for mood, keywords in (
            found_keywords.items()
        ):

            for keyword in keywords:

                if self.validate_keyword(
                    sentence,
                    mood,
                    keyword,
                ):

                    return True

        return False

    # ==========================================================
    # FULL SENTENCE ANALYSIS
    # ==========================================================

    def analyze_sentence(
        self,
        sentence: str,
    ):
        """
        Performs complete analysis of one sentence.

        Returns:

        {
            "valid": True,
            "positive": {
                "urban": ["modern", "city"],
                "quiet": ["peaceful"]
            },
            "negative": {
                "crowded": ["busy"]
            }
        }
        """

        found = self.find_keywords(
            sentence
        )

        positive = {}
        negative = {}

        for mood, keywords in found.items():

            for keyword in keywords:

                if self.is_negated(
                    sentence,
                    keyword,
                ):

                    negative.setdefault(
                        mood,
                        []
                    ).append(keyword)

                else:

                    positive.setdefault(
                        mood,
                        []
                    ).append(keyword)

        return {
            "valid": bool(
                positive
            ),

            "positive": positive,

            "negative": negative,
        }