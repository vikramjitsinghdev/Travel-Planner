class MoodScore:
    """
    Calculates numerical preference scores from the
    moods returned by MoodAgent.

    This class does NOT interpret user language.

    Its responsibilities are:
        - assign default importance to moods
        - distinguish wanted and rejected moods
        - produce weighted mood preferences
        - calculate destination compatibility later

    Score range:

        +1.0  = strongly wanted
         0.0  = neutral
        -1.0  = strongly avoided
    """

    def __init__(self):

        # --------------------------------------------------
        # Default importance of each supported mood.
        #
        # These values can later be changed based on
        # testing and user feedback.
        # --------------------------------------------------

        self.mood_weights = {

            # Nature / environment
            "nature": 1.0,
            "mountains": 1.0,
            "beaches": 1.0,
            "wildlife": 0.9,
            "remote": 0.9,

            # Activities
            "hiking": 0.9,
            "water_sports": 0.8,
            "adventure": 0.8,
            "road_trips": 0.7,
            "photography": 0.7,

            # Experience
            "relaxation": 0.8,
            "quiet": 0.9,
            "comfort": 0.7,
            "culture": 0.8,
            "history": 0.7,
            "food": 0.7,
            "architecture": 0.6,
            "museums": 0.6,
            "spirituality": 0.6,

            # Social / trip type
            "nightlife": 0.8,
            "shopping": 0.5,
            "luxury": 0.6,
            "romance": 0.8,
            "family": 0.9,
            "solo": 0.8,

            # Environment
            "snow": 0.8,
            "warm_weather": 0.8,
            "cold_weather": 0.8,

            # Urban / crowd
            "urban": 0.8,
            "crowded": 1.0,
        }

    # ==================================================
    # GET BASE WEIGHT
    # ==================================================

    def get_weight(self, mood):
        """
        Return the default importance of a mood.

        Unknown moods receive a neutral default value.
        """

        mood = str(mood).strip().lower()

        return self.mood_weights.get(
            mood,
            0.5
        )

    # ==================================================
    # SCORE WANTED MOODS
    # ==================================================

    def score_wanted(self, moods):
        """
        Give positive scores to wanted moods.

        Example:

            ["nature", "mountains", "hiking"]

        becomes:

            {
                "nature": 1.0,
                "mountains": 1.0,
                "hiking": 0.9
            }
        """

        scores = {}

        if not isinstance(moods, list):
            return scores

        for mood in moods:

            mood = str(
                mood
            ).strip().lower()

            if mood in self.mood_weights:

                scores[mood] = self.get_weight(
                    mood
                )

        return scores

    # ==================================================
    # SCORE REJECTED MOODS
    # ==================================================

    def score_avoided(self, moods):
        """
        Give negative scores to rejected moods.

        Example:

            ["crowded", "urban"]

        becomes:

            {
                "crowded": -1.0,
                "urban": -0.8
            }
        """

        scores = {}

        if not isinstance(moods, list):
            return scores

        for mood in moods:

            mood = str(
                mood
            ).strip().lower()

            if mood in self.mood_weights:

                scores[mood] = -self.get_weight(
                    mood
                )

        return scores

    # ==================================================
    # CREATE COMPLETE SCORE PROFILE
    # ==================================================

    def score_profile(self, profile):
        """
        Convert a MoodAgent profile into a complete
        numerical mood profile.

        Input:

            {
                "wanted": [
                    "nature",
                    "mountains"
                ],
                "avoid": [
                    "crowded",
                    "urban"
                ]
            }

        Output:

            {
                "nature": 1.0,
                "mountains": 1.0,
                "crowded": -1.0,
                "urban": -0.8
            }
        """

        if not isinstance(profile, dict):
            return {}

        wanted = profile.get(
            "wanted",
            []
        )

        avoid = profile.get(
            "avoid",
            []
        )

        scores = {}

        # Positive preferences.
        scores.update(
            self.score_wanted(
                wanted
            )
        )

        # Negative preferences.
        avoided_scores = self.score_avoided(
            avoid
        )

        scores.update(
            avoided_scores
        )

        return scores

    # ==================================================
    # CREATE DETAILED SCORE PROFILE
    # ==================================================

    def analyze_profile(self, profile):
        """
        Return a detailed scoring structure.

        This is useful for debugging and for showing
        the reasoning behind the eventual destination
        ranking system.
        """

        if not isinstance(profile, dict):
            profile = {}

        wanted = profile.get(
            "wanted",
            []
        )

        avoid = profile.get(
            "avoid",
            []
        )

        wanted_scores = self.score_wanted(
            wanted
        )

        avoided_scores = self.score_avoided(
            avoid
        )

        total_positive = sum(
            wanted_scores.values()
        )

        total_negative = sum(
            avoided_scores.values()
        )

        return {
            "wanted": wanted_scores,

            "avoid": avoided_scores,

            "combined": {
                **wanted_scores,
                **avoided_scores
            },

            "total_positive": round(
                total_positive,
                3
            ),

            "total_negative": round(
                total_negative,
                3
            )
        }

    # ==================================================
    # DESTINATION COMPATIBILITY
    # ==================================================

    def calculate_destination_score(
        self,
        user_scores,
        destination_moods
    ):
        """
        Calculate how well a destination matches
        the user's mood preferences.

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

        The destination's mood values should ideally
        be normalized between 0.0 and 1.0.

        A positive user preference rewards matching
        destination characteristics.

        A negative user preference penalizes them.
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

            destination_value = destination_moods.get(
                mood,
                0.0
            )

            try:
                user_score = float(
                    user_score
                )

                destination_value = float(
                    destination_value
                )

            except (
                TypeError,
                ValueError
            ):
                continue

            score += (
                user_score
                * destination_value
            )

        return round(
            score,
            3
        )