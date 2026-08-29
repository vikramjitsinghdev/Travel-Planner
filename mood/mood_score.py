class MoodScore:
    """
    Deterministic mood scoring system.

    This class does NOT understand natural language.

    MoodAgent/Groq decides:

        wanted
        avoid

    MoodKeywords decides:

        canonical mood names

    MoodScore decides:

        numerical importance

    ============================================================
    SCORE RANGE
    ============================================================

        +1.0  strongly desired
         0.0  neutral
        -1.0  strongly avoided

    ============================================================
    RESPONSIBILITIES
    ============================================================

    1. Assign default weights to supported moods.
    2. Give positive scores to wanted moods.
    3. Give negative scores to avoided moods.
    4. Produce detailed score information.
    5. Calculate destination compatibility.

    It does NOT:

        - interpret user language
        - determine wanted vs avoided
        - search for destinations
        - search the web
        - modify the budget
        - communicate with other agents
    """

    def __init__(self):

        # ======================================================
        # DEFAULT MOOD WEIGHTS
        # ======================================================

        self.mood_weights = {

            # --------------------------------------------------
            # Nature / Environment
            # --------------------------------------------------

            "nature": 1.0,
            "mountains": 1.0,
            "beaches": 1.0,
            "wildlife": 0.9,
            "remote": 0.9,

            # --------------------------------------------------
            # Activities
            # --------------------------------------------------

            "hiking": 0.9,
            "water_sports": 0.8,
            "adventure": 0.8,
            "road_trips": 0.7,
            "photography": 0.7,

            # --------------------------------------------------
            # Experience
            # --------------------------------------------------

            "relaxation": 0.8,
            "quiet": 0.9,
            "comfort": 0.7,
            "culture": 0.8,
            "history": 0.7,
            "food": 0.7,
            "architecture": 0.6,
            "museums": 0.6,
            "spirituality": 0.6,

            # --------------------------------------------------
            # Social / Trip Type
            # --------------------------------------------------

            "nightlife": 0.8,
            "shopping": 0.5,
            "luxury": 0.6,
            "romance": 0.8,
            "family": 0.9,
            "solo": 0.8,

            # --------------------------------------------------
            # Weather
            # --------------------------------------------------

            "snow": 0.8,
            "warm_weather": 0.8,
            "cold_weather": 0.8,

            # --------------------------------------------------
            # Urban / Crowd
            # --------------------------------------------------

            "urban": 0.8,
            "crowded": 1.0,
        }

    # ==========================================================
    # GET WEIGHT
    # ==========================================================

    def get_weight(
        self,
        mood
    ):
        """
        Return the default weight of a canonical mood.

        Unknown moods receive 0.5 as a neutral fallback.
        """

        mood = str(
            mood
        ).strip().lower()

        return self.mood_weights.get(
            mood,
            0.5
        )

    # ==========================================================
    # GET SUPPORTED MOODS
    # ==========================================================

    def get_supported_moods(self):
        """
        Return all moods that can be scored.
        """

        return list(
            self.mood_weights.keys()
        )

    # ==========================================================
    # SCORE WANTED
    # ==========================================================

    def score_wanted(
        self,
        moods
    ):
        """
        Assign positive scores to wanted moods.
        """

        scores = {}

        if not isinstance(
            moods,
            list
        ):

            return scores

        for mood in moods:

            mood = str(
                mood
            ).strip().lower()

            if mood in self.mood_weights:

                scores[mood] = (
                    self.get_weight(
                        mood
                    )
                )

        return scores

    # ==========================================================
    # SCORE AVOIDED
    # ==========================================================

    def score_avoided(
        self,
        moods
    ):
        """
        Assign negative scores to avoided moods.
        """

        scores = {}

        if not isinstance(
            moods,
            list
        ):

            return scores

        for mood in moods:

            mood = str(
                mood
            ).strip().lower()

            if mood in self.mood_weights:

                scores[mood] = -(
                    self.get_weight(
                        mood
                    )
                )

        return scores

    # ==========================================================
    # SCORE PROFILE
    # ==========================================================

    def score_profile(
        self,
        profile
    ):
        """
        Convert a canonical preference profile into
        numerical mood scores.
        """

        if not isinstance(
            profile,
            dict
        ):

            return {}

        wanted = profile.get(
            "wanted",
            []
        )

        avoid = profile.get(
            "avoid",
            []
        )

        wanted_scores = (
            self.score_wanted(
                wanted
            )
        )

        avoided_scores = (
            self.score_avoided(
                avoid
            )
        )

        scores = {}

        scores.update(
            wanted_scores
        )

        scores.update(
            avoided_scores
        )

        return scores

    # ==========================================================
    # ANALYZE PROFILE
    # ==========================================================

    def analyze_profile(
        self,
        profile
    ):
        """
        Return complete scoring information.

        Example:

        {
            "wanted": {
                "nature": 1.0,
                "mountains": 1.0
            },

            "avoid": {
                "crowded": -1.0
            },

            "combined": {
                "nature": 1.0,
                "mountains": 1.0,
                "crowded": -1.0
            },

            "total_positive": 2.0,

            "total_negative": -1.0
        }
        """

        if not isinstance(
            profile,
            dict
        ):

            profile = {}

        wanted = profile.get(
            "wanted",
            []
        )

        avoid = profile.get(
            "avoid",
            []
        )

        wanted_scores = (
            self.score_wanted(
                wanted
            )
        )

        avoided_scores = (
            self.score_avoided(
                avoid
            )
        )

        combined = {
            **wanted_scores,
            **avoided_scores
        }

        total_positive = sum(
            score
            for score in wanted_scores.values()
            if score > 0
        )

        total_negative = sum(
            score
            for score in avoided_scores.values()
            if score < 0
        )

        return {

            "wanted":
                wanted_scores,

            "avoid":
                avoided_scores,

            "combined":
                combined,

            "total_positive":
                round(
                    total_positive,
                    3
                ),

            "total_negative":
                round(
                    total_negative,
                    3
                )
        }

    # ==========================================================
    # CALCULATE DESTINATION SCORE
    # ==========================================================

    def calculate_destination_score(
        self,
        user_scores,
        destination_moods
    ):
        """
        Calculate destination compatibility.

        user_scores:

            {
                "nature": 1.0,
                "mountains": 1.0,
                "crowded": -1.0
            }

        destination_moods:

            {
                "nature": 0.9,
                "mountains": 1.0,
                "crowded": 0.2
            }

        Calculation:

            user_score × destination_value

        Positive user preferences reward matching
        characteristics.

        Negative user preferences penalize matching
        unwanted characteristics.

        This method will become useful when TravelAgent
        eventually ranks researched destinations.
        """

        if not isinstance(
            user_scores,
            dict
        ):

            return 0.0

        if not isinstance(
            destination_moods,
            dict
        ):

            return 0.0

        score = 0.0

        for mood, user_score in user_scores.items():

            try:

                user_score = float(
                    user_score
                )

                destination_value = float(
                    destination_moods.get(
                        mood,
                        0.0
                    )
                )

            except (
                TypeError,
                ValueError
            ):

                continue

            # Keep destination values within
            # the expected 0.0 - 1.0 range.

            destination_value = max(
                0.0,
                min(
                    1.0,
                    destination_value
                )
            )

            score += (
                user_score
                * destination_value
            )

        return round(
            score,
            3
        )

    # ==========================================================
    # NORMALIZED COMPATIBILITY
    # ==========================================================

    def calculate_normalized_score(
        self,
        user_scores,
        destination_moods
    ):
        """
        Return a normalized compatibility percentage.

        This is useful later when displaying something like:

            Compatibility: 87%

        The raw score remains available through
        calculate_destination_score().
        """

        if not isinstance(
            user_scores,
            dict
        ):

            return 0.0

        if not user_scores:

            return 0.0

        raw_score = (
            self.calculate_destination_score(
                user_scores,
                destination_moods
            )
        )

        # Maximum possible positive contribution.
        maximum = sum(
            abs(float(score))
            for score in user_scores.values()
            if float(score) > 0
        )

        if maximum <= 0:

            return 0.0

        # Convert to a simple percentage.
        normalized = (
            raw_score / maximum
        ) * 100

        # Keep result between 0 and 100.
        normalized = max(
            0.0,
            min(
                100.0,
                normalized
            )
        )

        return round(
            normalized,
            1
        )