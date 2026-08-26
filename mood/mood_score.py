# mood_score.py

import math


class MoodScore:
    """
    Calculates the percentage distribution of travel moods.

    Every mood has one of three states:

        SELECTED
            Gets:
                P_base + A * e^(-lambda * (r - 1))

        UNSELECTED
            Gets:
                P_base

        REJECTED
            Gets:
                0

    After calculating the raw scores, all NON-REJECTED moods
    are normalized so that their percentages add up to 100%.
    """

    def __init__(
        self,
        moods,
        base_percentage=1.0,
        amplitude=10.0,
        decay=0.5,
    ):
        """
        Parameters
        ----------
        moods:
            List of every available mood category.

        base_percentage:
            Base raw score given to every non-rejected mood.

        amplitude:
            Additional score given to the highest-ranked
            selected mood.

        decay:
            Controls how quickly the additional selected
            score decreases with rank.
        """

        self.moods = list(moods)

        self.base_percentage = base_percentage
        self.amplitude = amplitude
        self.decay = decay

    # ==========================================================
    # PARAMETERS
    # ==========================================================

    def set_parameters(
        self,
        base_percentage=None,
        amplitude=None,
        decay=None,
    ):
        """
        Updates the scoring parameters.
        """

        if base_percentage is not None:
            self.base_percentage = base_percentage

        if amplitude is not None:
            self.amplitude = amplitude

        if decay is not None:
            self.decay = decay

    # ==========================================================
    # SELECTED MOOD FORMULA
    # ==========================================================

    def selected_raw_score(
        self,
        rank,
    ):
        """
        Calculates the raw score of a selected mood.

        Formula:

            P_base + A * e^(-lambda * (r - 1))
        """

        return (
            self.base_percentage
            +
            self.amplitude
            * math.exp(
                -self.decay
                * (rank - 1)
            )
        )

    # ==========================================================
    # CLOSED-FORM SELECTED BONUS
    # ==========================================================

    def selected_bonus_sum(
        self,
        number_selected,
    ):
        """
        Calculates the total exponential bonus of all
        selected moods using the geometric-series formula.

        Formula:

            A * (1 - e^(-lambda*n))
              --------------------
                1 - e^(-lambda)

        This avoids manually summing every selected mood.
        """

        if number_selected <= 0:
            return 0.0

        # Special case where lambda = 0.
        #
        # e^0 = 1, so the normal formula would divide by zero.
        #
        # In that case every selected mood receives A.
        if self.decay == 0:

            return (
                self.amplitude
                * number_selected
            )

        ratio = math.exp(
            -self.decay
        )

        return (
            self.amplitude
            *
            (
                1 - ratio ** number_selected
            )
            /
            (
                1 - ratio
            )
        )

    # ==========================================================
    # TOTAL RAW SCORE
    # ==========================================================

    def calculate_total_raw_score(
        self,
        number_active,
        number_selected,
    ):
        """
        Calculates the total raw score S.

        IMPORTANT:

        Only NON-REJECTED categories participate.

        Therefore:

            S =
                m * P_base
                +
                A * geometric_sum

        where:

            m = number of non-rejected categories
            n = number of selected categories
        """

        if number_active <= 0:
            return 0.0

        if number_selected < 0:
            number_selected = 0

        if number_selected > number_active:
            number_selected = number_active

        base_total = (
            number_active
            * self.base_percentage
        )

        bonus_total = (
            self.selected_bonus_sum(
                number_selected
            )
        )

        return (
            base_total
            +
            bonus_total
        )

    # ==========================================================
    # CLEAN MOOD LIST
    # ==========================================================

    def _clean_moods(
        self,
        moods,
    ):
        """
        Removes invalid/duplicate moods while preserving
        their original order.
        """

        cleaned = []

        for mood in moods:

            if not mood:
                continue

            if mood not in self.moods:
                continue

            if mood not in cleaned:

                cleaned.append(
                    mood
                )

        return cleaned

    # ==========================================================
    # CALCULATE RAW POINTS
    # ==========================================================

    def calculate_raw_points(
        self,
        selected_moods,
        rejected_moods=None,
    ):
        """
        Creates the raw point distribution BEFORE normalization.

        States:

            selected   -> base + exponential bonus
            unselected -> base
            rejected   -> 0
        """

        if rejected_moods is None:
            rejected_moods = []

        selected_moods = self._clean_moods(
            selected_moods
        )

        rejected_moods = self._clean_moods(
            rejected_moods
        )

        # ------------------------------------------------------
        # Rejection always has priority.
        # ------------------------------------------------------

        selected_moods = [
            mood
            for mood in selected_moods
            if mood not in rejected_moods
        ]

        # ------------------------------------------------------
        # Number of categories that actually participate.
        # ------------------------------------------------------

        active_moods = [
            mood
            for mood in self.moods
            if mood not in rejected_moods
        ]

        raw_points = {}

        # ------------------------------------------------------
        # Calculate each category.
        # ------------------------------------------------------

        for mood in self.moods:

            # ----------------------------------------------
            # REJECTED
            # ----------------------------------------------

            if mood in rejected_moods:

                raw_points[mood] = 0.0

            # ----------------------------------------------
            # SELECTED
            # ----------------------------------------------

            elif mood in selected_moods:

                rank = (
                    selected_moods.index(mood)
                    + 1
                )

                raw_points[mood] = (
                    self.selected_raw_score(
                        rank
                    )
                )

            # ----------------------------------------------
            # UNSELECTED
            # ----------------------------------------------

            else:

                raw_points[mood] = (
                    self.base_percentage
                )

        return raw_points

    # ==========================================================
    # NORMALIZE
    # ==========================================================

    def normalize_scores(
        self,
        raw_points,
        rejected_moods=None,
    ):
        """
        Converts raw points into percentages.

        Rejected categories remain exactly 0%.

        Every other category participates in the denominator.

        Therefore:

            sum(all percentages) = 100%
        """

        if rejected_moods is None:
            rejected_moods = []

        rejected_moods = self._clean_moods(
            rejected_moods
        )

        # ------------------------------------------------------
        # IMPORTANT:
        #
        # DO NOT include rejected categories in the denominator.
        # ------------------------------------------------------

        total = sum(
            score
            for mood, score in raw_points.items()
            if mood not in rejected_moods
        )

        # ------------------------------------------------------
        # Safety check.
        # ------------------------------------------------------

        if total <= 0:

            active_moods = [
                mood
                for mood in self.moods
                if mood not in rejected_moods
            ]

            if not active_moods:

                return {
                    mood: 0.0
                    for mood in self.moods
                }

            equal_percentage = (
                100.0
                / len(active_moods)
            )

            return {
                mood: (
                    0.0
                    if mood in rejected_moods
                    else equal_percentage
                )
                for mood in self.moods
            }

        # ------------------------------------------------------
        # Normalize.
        # ------------------------------------------------------

        percentages = {}

        for mood, raw_score in (
            raw_points.items()
        ):

            if mood in rejected_moods:

                percentages[mood] = 0.0

            else:

                percentages[mood] = (
                    raw_score
                    / total
                ) * 100.0

        # ------------------------------------------------------
        # Correct floating-point rounding.
        # ------------------------------------------------------

        difference = (
            100.0
            - sum(percentages.values())
        )

        active_moods = [
            mood
            for mood in self.moods
            if mood not in rejected_moods
        ]

        if active_moods:

            # Add the tiny rounding correction to the largest
            # active category.
            largest_mood = max(
                active_moods,
                key=lambda mood:
                    percentages[mood]
            )

            percentages[largest_mood] += (
                difference
            )

        return percentages

    # ==========================================================
    # MAIN SCORING METHOD
    # ==========================================================

    def calculate_scores(
        self,
        selected_moods,
        rejected_moods=None,
    ):
        """
        Complete scoring pipeline:

            selected/rejected moods
                    ↓
                raw points
                    ↓
                normalization
                    ↓
                percentages totaling 100%
        """

        if rejected_moods is None:
            rejected_moods = []

        selected_moods = self._clean_moods(
            selected_moods
        )

        rejected_moods = self._clean_moods(
            rejected_moods
        )

        # ------------------------------------------------------
        # Calculate raw scores.
        # ------------------------------------------------------

        raw_points = (
            self.calculate_raw_points(
                selected_moods,
                rejected_moods,
            )
        )

        # ------------------------------------------------------
        # Normalize.
        # ------------------------------------------------------

        percentages = (
            self.normalize_scores(
                raw_points,
                rejected_moods,
            )
        )

        return percentages

    # ==========================================================
    # GET RANKING
    # ==========================================================

    def get_ranking(
        self,
        percentages,
    ):
        """
        Returns moods from highest to lowest percentage.
        """

        return sorted(
            percentages.items(),
            key=lambda item:
                item[1],
            reverse=True,
        )

    # ==========================================================
    # TOP MOODS
    # ==========================================================

    def get_top_moods(
        self,
        percentages,
        amount=5,
    ):
        """
        Returns the highest scoring moods.
        """

        return self.get_ranking(
            percentages
        )[:amount]

    # ==========================================================
    # DISPLAY
    # ==========================================================

    def display_scores(
        self,
        percentages,
    ):
        """
        Displays the final mood distribution.
        """

        print(
            "\nMOOD DISTRIBUTION"
        )

        print(
            "-" * 40
        )

        for mood, percentage in (
            self.get_ranking(
                percentages
            )
        ):

            print(
                f"{mood:<22}"
                f"{percentage:>7.2f}%"
            )

        print(
            "-" * 40
        )

        print(
            f"{'TOTAL':<22}"
            f"{sum(percentages.values()):>7.2f}%"
        )