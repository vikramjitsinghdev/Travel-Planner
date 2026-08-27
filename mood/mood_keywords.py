import re


class MoodKeywords:
    """
    Helper class for the MoodAgent.

    This class does NOT interpret the user's request.

    Groq/MoodAgent remains responsible for understanding
    the user's language.

    MoodKeywords is only responsible for:
        - storing supported mood categories
        - storing useful keyword/synonym vocabulary
        - finding keyword matches in text
        - validating AI-generated moods
        - normalizing mood names
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
                "forest",
                "forests",
                "woods",
                "woodlands",
                "valley",
                "valleys",
                "lake",
                "lakes",
                "river",
                "rivers",
                "waterfall",
                "waterfalls",
                "canyon",
                "canyons",
                "cliff",
                "cliffs",
                "national park",
                "national parks",
                "nature reserve",
                "nature reserves",
                "pristine nature",
                "untouched nature",
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
                "cafe",
                "cafes",
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
                "club",
                "clubs",
                "nightclub",
                "nightclubs",
                "night club",
                "night clubs",
                "bar",
                "bars",
                "pub",
                "pubs",
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
                "boutique",
                "boutiques",
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

        # Common expressions indicating rejection.
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

    def normalize(self, text):
        """
        Normalize text for searching and comparison.
        """

        text = str(text).lower().strip()

        text = text.replace("-", " ")

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text

    # ==========================================================
    # MOOD CATEGORIES
    # ==========================================================

    def get_moods(self):
        """
        Return all supported canonical mood categories.
        """

        return list(
            self.mood_keywords.keys()
        )

    # ==========================================================
    # KEYWORDS FOR MOOD
    # ==========================================================

    def get_keywords(self, mood):
        """
        Return keywords belonging to a specific mood.
        """

        mood = self.normalize(mood)

        return self.mood_keywords.get(
            mood,
            []
        )

    # ==========================================================
    # VALIDATE AI MOOD
    # ==========================================================

    def is_valid_mood(self, mood):
        """
        Check whether an AI-generated mood is supported
        by the application's mood vocabulary.
        """

        mood = self.normalize(mood)

        return mood in self.mood_keywords

    # ==========================================================
    # VALIDATE MOOD LIST
    # ==========================================================

    def validate_mood_list(self, moods):
        """
        Clean a list of moods returned by the AI.

        Invalid moods are removed.
        Duplicate moods are removed.
        """

        if not isinstance(moods, list):
            return []

        valid = []

        for mood in moods:

            mood = self.normalize(mood)

            if (
                self.is_valid_mood(mood)
                and mood not in valid
            ):
                valid.append(mood)

        return valid

    # ==========================================================
    # SEARCH KEYWORD
    # ==========================================================

    def search_keyword(self, text, keyword):
        """
        Check whether a keyword appears in text.

        Handles:
            - capitalization
            - hyphen differences
            - whole-word matching
        """

        text = self.normalize(text)
        keyword = self.normalize(keyword)

        pattern = (
            rf"(?<!\w)"
            rf"{re.escape(keyword)}"
            rf"(?!\w)"
        )

        return bool(
            re.search(
                pattern,
                text
            )
        )

    # ==========================================================
    # FIND MOODS IN USER INPUT
    # ==========================================================

    def find_moods(self, text):
        """
        Find mood categories that have explicit keyword
        matches inside the user's input.

        IMPORTANT:
        This is only a helper.

        MoodAgent/Groq remains the primary interpreter.
        """

        found = []

        for mood, keywords in self.mood_keywords.items():

            for keyword in keywords:

                if self.search_keyword(
                    text,
                    keyword
                ):

                    if mood not in found:
                        found.append(mood)

                    break

        return found

    # ==========================================================
    # FIND ACTUAL KEYWORDS
    # ==========================================================

    def find_keywords(self, text):
        """
        Return the actual vocabulary matches.

        Example:

        {
            "mountains": ["mountain"],
            "hiking": ["hiking"],
            "quiet": ["peaceful"]
        }
        """

        found = {}

        for mood, keywords in self.mood_keywords.items():

            matches = []

            for keyword in keywords:

                if self.search_keyword(
                    text,
                    keyword
                ):

                    matches.append(keyword)

            if matches:
                found[mood] = matches

        return found

    # ==========================================================
    # NEGATION DETECTION
    # ==========================================================

    def is_negated(self, text, keyword):
        """
        Detect whether a keyword appears to be rejected.

        This is a basic helper only.

        The AI remains responsible for understanding
        complicated language and context.
        """

        text = self.normalize(text)
        keyword = self.normalize(keyword)

        position = text.find(keyword)

        if position == -1:
            return False

        before = text[:position]

        for phrase in self.negation_phrases:

            if phrase in before:
                return True

        recent_words = before.split()[-5:]

        if any(
            word in {"not", "no", "never"}
            for word in recent_words
        ):
            return True

        return False

    # ==========================================================
    # ANALYZE EXPLICIT KEYWORDS
    # ==========================================================

    def analyze(self, text):
        """
        Analyze explicit vocabulary found in user input.

        Returns:

        {
            "wanted": [...],
            "avoid": [...],
            "keywords": {...}
        }

        This does NOT replace Groq.
        """

        found = self.find_keywords(text)

        wanted = []
        avoid = []

        for mood, keywords in found.items():

            for keyword in keywords:

                if self.is_negated(
                    text,
                    keyword
                ):

                    if mood not in avoid:
                        avoid.append(mood)

                else:

                    if mood not in wanted:
                        wanted.append(mood)

        return {
            "wanted": wanted,
            "avoid": avoid,
            "keywords": found
        }

    # ==========================================================
    # VALIDATE GROQ PROFILE
    # ==========================================================

    def validate_profile(self, profile):
        """
        Validate the mood portions of a profile returned
        by Groq.

        The AI still determines the meaning.

        This helper only makes sure the returned mood names
        exist in the application's vocabulary.
        """

        if not isinstance(profile, dict):
            return {
                "wanted": [],
                "avoid": [],
                "summary": ""
            }

        wanted = self.validate_mood_list(
            profile.get(
                "wanted",
                []
            )
        )

        avoid = self.validate_mood_list(
            profile.get(
                "avoid",
                []
            )
        )

        # If a mood is both wanted and rejected,
        # rejection takes priority.
        wanted = [
            mood
            for mood in wanted
            if mood not in avoid
        ]

        return {
            "wanted": wanted,
            "avoid": avoid,
            "summary": profile.get(
                "summary",
                ""
            )
        }