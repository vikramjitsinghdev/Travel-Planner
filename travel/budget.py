class Budget:
    """
    Travel budget manager.

    Budget maintains the financial state of the current
    travel-planning session.

    IMPORTANT ARCHITECTURE:

        main.py
           |
           +---- Budget
           |
           +---- TravelAgent
           |
           +---- ResearchAgent
           |
           +---- MapService

    Budget does NOT communicate directly with any AI agent
    or external API.

    main.py is responsible for passing budget information
    between the systems.

    The Budget class distinguishes between:

        1. Estimated costs
        2. Confirmed expenses

    Estimated costs are temporary planning information.

    Confirmed expenses actually reduce the remaining budget.
    """

    def __init__(
        self,
        total_budget,
        currency="CAD"
    ):
        """
        Create a new travel budget.

        Example:

            Budget(2000)

        creates:

            Total budget = 2000 CAD
        """

        if total_budget is None:

            raise ValueError(
                "A budget amount is required."
            )

        try:

            total_budget = float(
                total_budget
            )

        except (
            TypeError,
            ValueError
        ):

            raise ValueError(
                "Budget must be a valid number."
            )

        if total_budget < 0:

            raise ValueError(
                "Budget cannot be negative."
            )

        self.total_budget = round(
            total_budget,
            2
        )

        self.currency = str(
            currency
        ).upper()

        # ------------------------------------------------------
        # Confirmed money already committed/spent.
        # ------------------------------------------------------

        self.spent = 0.0

        # ------------------------------------------------------
        # Temporary estimated costs.
        #
        # These do NOT reduce remaining budget.
        # ------------------------------------------------------

        self.estimated_costs = []

        self.estimated_total = 0.0

        # ------------------------------------------------------
        # Confirmed expenses.
        # ------------------------------------------------------

        self.expenses = []

        # ------------------------------------------------------
        # Current remaining budget.
        # ------------------------------------------------------

        self.remaining = self.total_budget

    # ==========================================================
    # ADD ESTIMATED COST
    # ==========================================================

    def add_estimate(
        self,
        amount,
        category,
        description=""
    ):
        """
        Add a temporary estimated travel cost.

        Estimated costs are used while planning.

        They DO NOT reduce the user's remaining budget.

        Example:

            budget.add_estimate(
                500,
                "flight",
                "Estimated round-trip flight"
            )
        """

        amount = self._validate_amount(
            amount,
            "Estimated cost"
        )

        estimate = {
            "amount": amount,
            "category": str(
                category
            ),
            "description": str(
                description
            )
        }

        self.estimated_costs.append(
            estimate
        )

        self.estimated_total = round(
            self.estimated_total + amount,
            2
        )

        return estimate.copy()

    # ==========================================================
    # ADD MULTIPLE ESTIMATES
    # ==========================================================

    def add_estimates(
        self,
        estimates
    ):
        """
        Add multiple temporary estimated costs.

        Expected format:

            [
                {
                    "amount": 500,
                    "category": "flight",
                    "description": "Round trip"
                },
                {
                    "amount": 700,
                    "category": "hotel",
                    "description": "5 nights"
                }
            ]

        Returns the updated estimated costs.
        """

        if not isinstance(
            estimates,
            list
        ):

            raise TypeError(
                "estimates must be a list."
            )

        for estimate in estimates:

            if not isinstance(
                estimate,
                dict
            ):

                raise ValueError(
                    "Each estimate must be a dictionary."
                )

            self.add_estimate(
                amount=estimate.get(
                    "amount"
                ),
                category=estimate.get(
                    "category",
                    "other"
                ),
                description=estimate.get(
                    "description",
                    ""
                )
            )

        return self.get_estimates()

    # ==========================================================
    # GET ESTIMATES
    # ==========================================================

    def get_estimates(self):
        """
        Return all temporary estimated costs.
        """

        return {
            "estimated_total": round(
                self.estimated_total,
                2
            ),
            "currency": self.currency,
            "estimated_costs": [
                estimate.copy()
                for estimate in self.estimated_costs
            ]
        }

    # ==========================================================
    # CHECK ESTIMATED TRIP AFFORDABILITY
    # ==========================================================

    def estimate_is_affordable(
        self
    ):
        """
        Determine whether all current estimated costs
        could fit within the remaining budget.

        This does NOT commit any expenses.
        """

        return (
            self.estimated_total
            <= self.remaining
        )

    # ==========================================================
    # GET ESTIMATED REMAINING
    # ==========================================================

    def get_estimated_remaining(self):
        """
        Return the amount that would remain if all
        current estimates were committed.

        This does NOT actually spend anything.
        """

        return round(
            self.remaining
            - self.estimated_total,
            2
        )

    # ==========================================================
    # CONFIRM ESTIMATES
    # ==========================================================

    def confirm_estimates(self):
        """
        Convert the current estimated costs into
        confirmed expenses.

        This is intended to be called only after the
        user chooses to proceed with the planned trip.

        Example workflow:

            Research
                ↓
            Estimated costs
                ↓
            User confirms trip
                ↓
            confirm_estimates()
        """

        if not self.estimate_is_affordable():

            raise ValueError(
                "Estimated costs exceed the remaining budget."
            )

        for estimate in self.estimated_costs:

            self.expenses.append(
                estimate.copy()
            )

        self.spent = round(
            self.spent
            + self.estimated_total,
            2
        )

        self.remaining = round(
            self.total_budget
            - self.spent,
            2
        )

        self.clear_estimates()

        return self.get_status()

    # ==========================================================
    # ADD CONFIRMED EXPENSE
    # ==========================================================

    def add_expense(
        self,
        amount,
        category,
        description=""
    ):
        """
        Add a confirmed expense.

        This immediately reduces the remaining budget.

        Use this for costs that have actually been
        selected/confirmed by the user.
        """

        amount = self._validate_amount(
            amount,
            "Expense"
        )

        if amount > self.remaining:

            raise ValueError(
                "Expense exceeds the remaining budget."
            )

        expense = {
            "amount": amount,
            "category": str(
                category
            ),
            "description": str(
                description
            )
        }

        self.expenses.append(
            expense
        )

        self.spent = round(
            self.spent + amount,
            2
        )

        self.remaining = round(
            self.total_budget - self.spent,
            2
        )

        return expense.copy()

    # ==========================================================
    # ADD MULTIPLE CONFIRMED EXPENSES
    # ==========================================================

    def add_expenses(
        self,
        expenses
    ):
        """
        Add multiple confirmed expenses.

        Each expense is validated before being committed.
        """

        if not isinstance(
            expenses,
            list
        ):

            raise TypeError(
                "expenses must be a list."
            )

        total = 0.0

        for expense in expenses:

            if not isinstance(
                expense,
                dict
            ):

                raise ValueError(
                    "Each expense must be a dictionary."
                )

            amount = self._validate_amount(
                expense.get(
                    "amount"
                ),
                "Expense"
            )

            total += amount

        if total > self.remaining:

            raise ValueError(
                "Expenses exceed the remaining budget."
            )

        for expense in expenses:

            self.add_expense(
                amount=expense.get(
                    "amount"
                ),
                category=expense.get(
                    "category",
                    "other"
                ),
                description=expense.get(
                    "description",
                    ""
                )
            )

        return self.get_status()

    # ==========================================================
    # CLEAR ESTIMATES
    # ==========================================================

    def clear_estimates(self):
        """
        Remove all temporary estimated costs.

        This is useful when:

            - User changes destinations.
            - User changes budget.
            - A search is discarded.
            - A new trip search begins.
        """

        self.estimated_costs = []

        self.estimated_total = 0.0

    # ==========================================================
    # CHECK REMAINING
    # ==========================================================

    def get_remaining(self):
        """
        Return confirmed remaining budget.
        """

        return round(
            self.remaining,
            2
        )

    # ==========================================================
    # CHECK SPENT
    # ==========================================================

    def get_spent(self):
        """
        Return confirmed spending.
        """

        return round(
            self.spent,
            2
        )

    # ==========================================================
    # CHECK TOTAL
    # ==========================================================

    def get_total(self):
        """
        Return original total budget.
        """

        return round(
            self.total_budget,
            2
        )

    # ==========================================================
    # CHECK STATUS
    # ==========================================================

    def get_status(self):
        """
        Return the complete current budget state.

        This is the main method that main.py should pass
        to TravelAgent, ResearchAgent, MapService, etc.
        """

        return {
            "total_budget": round(
                self.total_budget,
                2
            ),

            "spent": round(
                self.spent,
                2
            ),

            "remaining": round(
                self.remaining,
                2
            ),

            "currency": self.currency,

            "estimated_total": round(
                self.estimated_total,
                2
            ),

            "estimated_remaining": round(
                self.get_estimated_remaining(),
                2
            ),

            "estimates_affordable": (
                self.estimate_is_affordable()
            ),

            "estimated_costs": [
                estimate.copy()
                for estimate in self.estimated_costs
            ],

            "expenses": [
                expense.copy()
                for expense in self.expenses
            ]
        }

    # ==========================================================
    # CHECK WHETHER AN EXPENSE IS AFFORDABLE
    # ==========================================================

    def can_afford(
        self,
        amount
    ):
        """
        Check whether a confirmed expense can fit
        within the remaining budget.

        This does NOT add the expense.
        """

        try:

            amount = float(
                amount
            )

        except (
            TypeError,
            ValueError
        ):

            return False

        if amount < 0:

            return False

        return (
            amount <= self.remaining
        )

    # ==========================================================
    # CHECK WHETHER AN ENTIRE TRIP IS AFFORDABLE
    # ==========================================================

    def can_afford_trip(
        self,
        total_estimated_cost
    ):
        """
        Check whether an entire estimated trip fits
        within the remaining budget.

        This does NOT commit the costs.
        """

        try:

            total_estimated_cost = float(
                total_estimated_cost
            )

        except (
            TypeError,
            ValueError
        ):

            return False

        if total_estimated_cost < 0:

            return False

        return (
            total_estimated_cost
            <= self.remaining
        )

    # ==========================================================
    # RESET EVERYTHING
    # ==========================================================

    def reset(self):
        """
        Completely reset the budget.

        This removes:

            - confirmed expenses
            - temporary estimates
            - spending

        The original total budget remains unchanged.
        """

        self.spent = 0.0

        self.remaining = (
            self.total_budget
        )

        self.expenses = []

        self.clear_estimates()

    # ==========================================================
    # INTERNAL VALIDATION
    # ==========================================================

    @staticmethod
    def _validate_amount(
        amount,
        label="Amount"
    ):
        """
        Validate and normalize a monetary amount.
        """

        try:

            amount = float(
                amount
            )

        except (
            TypeError,
            ValueError
        ):

            raise ValueError(
                f"{label} must be a valid number."
            )

        if amount < 0:

            raise ValueError(
                f"{label} cannot be negative."
            )

        return round(
            amount,
            2
        )