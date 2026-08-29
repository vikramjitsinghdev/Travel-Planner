class Budget:
    """
    Travel budget manager for the AI Travel Planner.

    Budget has two separate financial states:

        1. TEMPORARY ESTIMATES
           --------------------------------
           Used while the user is researching
           and comparing possible trips.

           These do NOT reduce the actual budget.

        2. CONFIRMED EXPENSES
           --------------------------------
           Created only after the user confirms
           a selected trip.

           These DO reduce the remaining budget.

    Main workflow:

        Candidate Trip
             ↓
        Cost Research
             ↓
        set_estimates()
             ↓
        User reviews
             ↓
        ┌───────────────┐
        │               │
      Change          Confirm
        │               │
        ↓               ↓
      clear        confirm_estimates()
        │               │
        └───────┐       ↓
                │    COMMITTED
                │
                ↓
          New Estimate


    IMPORTANT:

    Budget does NOT:

        - search for destinations
        - search for flights
        - search for hotels
        - communicate with Gemini
        - communicate with Ollama
        - communicate with MapTiler
        - decide which trip is best

    main.py controls communication between the
    Budget and the other systems.
    """

    # ==========================================================
    # INITIALIZATION
    # ==========================================================

    def __init__(
        self,
        total_budget,
        currency="CAD"
    ):
        """
        Create a new travel budget.

        Example:

            Budget(5000)

        creates:

            Total budget = 5000 CAD
            Spent = 0 CAD
            Remaining = 5000 CAD
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
        # Confirmed spending.
        # ------------------------------------------------------

        self.spent = 0.0

        # ------------------------------------------------------
        # Confirmed expenses.
        # ------------------------------------------------------

        self.expenses = []

        # ------------------------------------------------------
        # Temporary trip estimate.
        #
        # This represents the trip currently being
        # considered by the user.
        # ------------------------------------------------------

        self.estimated_costs = []

        self.estimated_total = 0.0

        # ------------------------------------------------------
        # Actual remaining budget.
        # ------------------------------------------------------

        self.remaining = self.total_budget

    # ==========================================================
    # ADD ONE TEMPORARY ESTIMATE
    # ==========================================================

    def add_estimate(
        self,
        amount,
        category,
        description=""
    ):
        """
        Add one temporary estimated trip cost.

        Example:

            budget.add_estimate(
                800,
                "accommodation",
                "7 nights hotel"
            )

        IMPORTANT:

        This does NOT reduce the actual remaining
        budget.
        """

        amount = self._validate_amount(
            amount,
            "Estimated cost"
        )

        if not category:
            category = "other"

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
    # ADD MULTIPLE TEMPORARY ESTIMATES
    # ==========================================================

    def add_estimates(
        self,
        estimates
    ):
        """
        Add multiple temporary estimated costs.

        Example:

            [
                {
                    "amount": 500,
                    "category": "transportation",
                    "description": "Fuel"
                },
                {
                    "amount": 1200,
                    "category": "accommodation",
                    "description": "7 nights"
                }
            ]

        Returns the current estimate state.
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
    # REPLACE CURRENT TRIP ESTIMATE
    # ==========================================================

    def set_estimates(
        self,
        estimates
    ):
        """
        Replace the current temporary trip estimate.

        This is the preferred method for main.py.

        Example workflow:

            Trip A
              ↓
            $4,500 estimate
              ↓
            User changes destination
              ↓
            set_estimates(Trip B)
              ↓
            Trip B replaces Trip A

        No confirmed spending is affected.
        """

        if not isinstance(
            estimates,
            list
        ):
            raise TypeError(
                "estimates must be a list."
            )

        # Remove previous temporary estimate.

        self.clear_estimates()

        # Add the new estimate.

        self.add_estimates(
            estimates
        )

        return self.get_status()

    # ==========================================================
    # GET CURRENT ESTIMATES
    # ==========================================================

    def get_estimates(self):
        """
        Return the current temporary trip estimate.
        """

        return {
            "estimated_total": round(
                self.estimated_total,
                2
            ),

            "currency": self.currency,

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
            ]
        }

    # ==========================================================
    # CHECK ESTIMATE AFFORDABILITY
    # ==========================================================

    def estimate_is_affordable(self):
        """
        Determine whether the current temporary
        trip estimate fits within the actual
        remaining budget.

        Does NOT commit anything.
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
        Calculate how much money would remain if
        the current temporary trip were confirmed.

        Does NOT modify the actual budget.
        """

        return round(
            self.remaining
            - self.estimated_total,
            2
        )

    # ==========================================================
    # CONFIRM CURRENT TRIP
    # ==========================================================

    def confirm_estimates(self):
        """
        Commit the current temporary trip estimate
        to the actual budget.

        This should only be called AFTER the user
        confirms the trip.

        Workflow:

            Temporary estimate
                    ↓
              User confirms
                    ↓
          confirm_estimates()
                    ↓
           Confirmed expenses
                    ↓
             Budget reduced
        """

        if not self.estimate_is_affordable():

            raise ValueError(
                "The selected trip exceeds the "
                "remaining budget."
            )

        if not self.estimated_costs:

            raise ValueError(
                "There are no estimated costs to confirm."
            )

        # ------------------------------------------------------
        # Move temporary costs into confirmed expenses.
        # ------------------------------------------------------

        for estimate in self.estimated_costs:

            self.expenses.append(
                estimate.copy()
            )

        # ------------------------------------------------------
        # Update actual spending.
        # ------------------------------------------------------

        self.spent = round(
            self.spent
            + self.estimated_total,
            2
        )

        # ------------------------------------------------------
        # Update actual remaining budget.
        # ------------------------------------------------------

        self.remaining = round(
            self.total_budget
            - self.spent,
            2
        )

        # ------------------------------------------------------
        # Remove temporary estimate.
        # ------------------------------------------------------

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
        Add an expense directly to the confirmed budget.

        Use this only when the application has a reason
        to immediately commit a cost.

        For the normal trip-selection workflow,
        main.py should generally use:

            set_estimates()
            confirm_estimates()

        instead.
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

        All expenses are validated before anything
        is committed.
        """

        if not isinstance(
            expenses,
            list
        ):
            raise TypeError(
                "expenses must be a list."
            )

        validated = []

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

            validated.append(
                {
                    "amount": amount,

                    "category": str(
                        expense.get(
                            "category",
                            "other"
                        )
                    ),

                    "description": str(
                        expense.get(
                            "description",
                            ""
                        )
                    )
                }
            )

            total += amount

        if total > self.remaining:

            raise ValueError(
                "Expenses exceed the remaining budget."
            )

        # ------------------------------------------------------
        # Commit only after everything has been validated.
        # ------------------------------------------------------

        for expense in validated:

            self.expenses.append(
                expense.copy()
            )

        self.spent = round(
            self.spent + total,
            2
        )

        self.remaining = round(
            self.total_budget - self.spent,
            2
        )

        return self.get_status()

    # ==========================================================
    # CLEAR TEMPORARY ESTIMATE
    # ==========================================================

    def clear_estimates(self):
        """
        Discard the current temporary trip estimate.

        Used when:

            - user changes destination
            - user changes trip requirements
            - user rejects the trip
            - a new search begins

        Confirmed spending is NOT affected.
        """

        self.estimated_costs = []

        self.estimated_total = 0.0

    # ==========================================================
    # CHECK ACTUAL REMAINING BUDGET
    # ==========================================================

    def get_remaining(self):
        """
        Return the actual confirmed remaining budget.
        """

        return round(
            self.remaining,
            2
        )

    # ==========================================================
    # CHECK ACTUAL SPENDING
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
    # CHECK TOTAL BUDGET
    # ==========================================================

    def get_total(self):
        """
        Return the original total budget.
        """

        return round(
            self.total_budget,
            2
        )

    # ==========================================================
    # COMPLETE STATUS
    # ==========================================================

    def get_status(self):
        """
        Return the complete financial state.

        This is the primary method that main.py
        should pass to the AI systems.
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

            # --------------------------------------------------
            # Temporary trip estimate
            # --------------------------------------------------

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

            # --------------------------------------------------
            # Confirmed spending
            # --------------------------------------------------

            "expenses": [
                expense.copy()
                for expense in self.expenses
            ]
        }

    # ==========================================================
    # CHECK SINGLE EXPENSE
    # ==========================================================

    def can_afford(
        self,
        amount
    ):
        """
        Check whether an amount fits within the
        actual remaining budget.

        Does NOT modify anything.
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
    # CHECK ENTIRE TRIP
    # ==========================================================

    def can_afford_trip(
        self,
        total_estimated_cost
    ):
        """
        Check whether an entire trip can fit within
        the actual remaining budget.

        Does NOT modify anything.
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
    # RESET
    # ==========================================================

    def reset(self):
        """
        Completely reset the current budget.

        The original total budget remains unchanged.
        """

        self.spent = 0.0

        self.remaining = (
            self.total_budget
        )

        self.expenses = []

        self.clear_estimates()

    # ==========================================================
    # INTERNAL AMOUNT VALIDATION
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