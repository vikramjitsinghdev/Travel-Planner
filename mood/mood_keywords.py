import re


class MoodKeywords:
    """
    Deterministic vocabulary and normalization helper.

    This class does NOT understand the user's overall sentence.

    MoodAgent/Groq is responsible for:
        - understanding context
        - understanding negation
        - deciding wanted vs avoided

    MoodKeywords is responsible for:
        - canonical mood vocabulary
        - synonyms
        - phrase normalization
        - validating moods
        - mapping phrases to canonical moods
        - basic keyword detection
        - preserving separation between mood and constraints

    It does NOT:
        - recommend destinations
        - search the internet
        - calculate prices
        - score destinations
        - communicate with TravelAgent
        - communicate with ResearchAgent
        - communicate with MapService
    """

    def __init__(self):

        # ======================================================
        # CANONICAL MOOD VOCABULARY
        # ======================================================

        self.mood_keywords = {

            # --------------------------------------------------
            # NATURE / ENVIRONMENT
            # --------------------------------------------------

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
                "beautiful scenery",
                "beautiful landscape",
            ],

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
                "ocean",
                "ocean experience",
                "ocean view",
                "ocean views",
            ],

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
                "wildlife reserve",
            ],

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

            # --------------------------------------------------
            # ACTIVITIES
            # --------------------------------------------------

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

            "road_trips": [
                "road trip",
                "road trips",
                "roadtrip",
                "roadtrips",
                "driving trip",
                "driving trips",
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

            # --------------------------------------------------
            # EXPERIENCE
            # --------------------------------------------------

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
            ],

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

            # --------------------------------------------------
            # CULTURE / HISTORY
            # --------------------------------------------------

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

            # --------------------------------------------------
            # SOCIAL / TRIP TYPE
            # --------------------------------------------------

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

            # --------------------------------------------------
            # WEATHER
            # --------------------------------------------------

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

            # --------------------------------------------------
            # URBAN / CROWD
            # --------------------------------------------------

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
            ],
        }

        # ======================================================
        # BASIC NEGATION VOCABULARY
        # ======================================================

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
            "minimize",
            "less",
            "fewer",
            "rather not",
        ]

        # ======================================================
        # DIRECT SEMANTIC NORMALIZATION
        # ======================================================
        #
        # Used by MoodAgent after Groq has already decided
        # whether the phrase is wanted or avoided.
        #
        # ======================================================

        self.semantic_mappings = {

            "natural": ["nature"],
            "natural beauty": ["nature"],
            "beautiful nature": ["nature"],
            "scenic nature": ["nature"],
            "beautiful scenery": ["nature"],
            "beautiful landscape": ["nature"],
            "scenic": ["nature"],

            "peaceful": ["quiet", "relaxation"],
            "peace": ["quiet", "relaxation"],
            "tranquil": ["quiet", "relaxation"],
            "tranquility": ["quiet", "relaxation"],
            "serene": ["quiet", "relaxation"],
            "serenity": ["quiet", "relaxation"],

            "relaxing": ["relaxation"],
            "relaxed": ["relaxation"],
            "relax": ["relaxation"],
            "restful": ["relaxation"],

            "mountain": ["mountains"],
            "mountainous": ["mountains"],
            "alpine": ["mountains"],

            "hiking trails": ["hiking"],
            "trekking": ["hiking"],
            "trek": ["hiking"],

            "city": ["urban"],
            "cities": ["urban"],
            "urban areas": ["urban"],
            "urban environments": ["urban"],

            "busy cities": ["urban", "crowded"],
            "crowded cities": ["urban", "crowded"],
            "crowded areas": ["crowded"],
            "crowded places": ["crowded"],
            "crowded tourist areas": ["crowded"],

            "night life": ["nightlife"],

            "ocean": ["beaches"],
            "ocean experience": ["beaches"],
            "oceanfront": ["beaches"],
            "coastal": ["beaches"],

            "party atmosphere": ["nightlife"],
            "party scene": ["nightlife"],
        }

    # ==========================================================
    # NORMALIZE TEXT
    # ==========================================================

    def normalize(self, text):
        """
        Normalize text for deterministic comparison.

        Handles:
            - capitalization
            - hyphens
            - repeated spaces
        """

        if text is None:
            return ""

        text = str(text).lower().strip()

        text = text.replace("-", " ")

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text

    # ==========================================================
    # GET SUPPORTED MOODS
    # ==========================================================

    def get_moods(self):
        """
        Return all canonical mood categories.
        """

        return list(
            self.mood_keywords.keys()
        )

    # ==========================================================
    # GET KEYWORDS
    # ==========================================================

    def get_keywords(self, mood):
        """
        Return all keywords belonging to a mood.
        """

        mood = self.normalize(mood)

        return self.mood_keywords.get(
            mood,
            []
        )

    # ==========================================================
    # VALIDATE MOOD
    # ==========================================================

    def is_valid_mood(self, mood):
        """
        Determine whether a value is a supported canonical
        mood.
        """

        mood = self.normalize(mood)

        return mood in self.mood_keywords

    # ==========================================================
    # VALIDATE MOOD LIST
    # ==========================================================

    def validate_mood_list(self, moods):
        """
        Remove invalid and duplicate moods.
        """

        if not isinstance(
            moods,
            list
        ):
            return []

        valid = []

        for mood in moods:

            mood = self.normalize(
                mood
            )

            if (
                self.is_valid_mood(mood)
                and mood not in valid
            ):

                valid.append(
                    mood
                )

        return valid

    # ==========================================================
    # NORMALIZE MOOD PHRASE
    # ==========================================================

    def normalize_mood_phrase(self, phrase):
        """
        Convert a phrase into canonical mood categories.

        Example:

            "beautiful nature"
                ->
            ["nature"]

            "peaceful"
                ->
            ["quiet", "relaxation"]
        """

        phrase = self.normalize(
            phrase
        )

        if not phrase:
            return []

        # Direct canonical mood.
        if self.is_valid_mood(
            phrase
        ):

            return [phrase]

        # Semantic mapping.
        if phrase in self.semantic_mappings:

            return list(
                self.semantic_mappings[
                    phrase
                ]
            )

        # Vocabulary search.
        return self.find_moods(
            phrase
        )

    # ==========================================================
    # SEARCH KEYWORD
    # ==========================================================

    def search_keyword(
        self,
        text,
        keyword
    ):
        """
        Check whether a keyword occurs in text.

        Uses whole-word matching.
        """

        text = self.normalize(
            text
        )

        keyword = self.normalize(
            keyword
        )

        if not text or not keyword:
            return False

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
    # FIND MOODS
    # ==========================================================

    def find_moods(self, text):
        """
        Find canonical moods represented by text.

        IMPORTANT:

        This is a lexical helper only.

        It does NOT determine wanted vs avoided.
        """

        found = []

        for mood, keywords in self.mood_keywords.items():

            for keyword in keywords:

                if self.search_keyword(
                    text,
                    keyword
                ):

                    if mood not in found:

                        found.append(
                            mood
                        )

                    break

        return found

    # ==========================================================
    # FIND ACTUAL KEYWORDS
    # ==========================================================

    def find_keywords(self, text):
        """
        Return the exact vocabulary matches found.
        """

        found = {}

        for mood, keywords in self.mood_keywords.items():

            matches = []

            for keyword in keywords:

                if self.search_keyword(
                    text,
                    keyword
                ):

                    matches.append(
                        keyword
                    )

            if matches:

                found[mood] = matches

        return found

    # ==========================================================
    # BASIC NEGATION CHECK
    # ==========================================================

    def is_negated(
        self,
        text,
        keyword
    ):
        """
        Basic negation detection.

        This is NOT intended to replace Groq.

        Groq remains responsible for contextual interpretation.
        """

        text = self.normalize(
            text
        )

        keyword = self.normalize(
            keyword
        )

        position = text.find(
            keyword
        )

        if position == -1:
            return False

        before = text[:position]

        for phrase in self.negation_phrases:

            if phrase in before:

                return True

        recent_words = before.split()[-5:]

        if any(
            word in {
                "not",
                "no",
                "never"
            }
            for word in recent_words
        ):

            return True

        return False

    # ==========================================================
    # KEYWORD ANALYSIS
    # ==========================================================

    def analyze(self, text):
        """
        Perform deterministic keyword analysis.

        This remains a helper/testing function.

        MoodAgent should use Groq as the primary source
        of contextual meaning.
        """

        found = self.find_keywords(
            text
        )

        wanted = []
        avoid = []

        for mood, keywords in found.items():

            for keyword in keywords:

                if self.is_negated(
                    text,
                    keyword
                ):

                    if mood not in avoid:

                        avoid.append(
                            mood
                        )

                else:

                    if mood not in wanted:

                        wanted.append(
                            mood
                        )

        # Prevent conflicts.
        wanted = [
            mood
            for mood in wanted
            if mood not in avoid
        ]

        return {
            "wanted": wanted,
            "avoid": avoid,
            "keywords": found
        }

    # ==========================================================
    # VALIDATE GROQ PROFILE
    # ==========================================================

    def validate_profile(
        self,
        profile
    ):
        """
        Validate the mood portion of a Groq result.

        Constraints are deliberately preserved separately.
        """

        if not isinstance(
            profile,
            dict
        ):

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

        # Avoid takes priority.
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