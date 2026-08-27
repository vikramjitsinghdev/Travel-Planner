class Budget:
    """
    Basic travel budget manager.

    This class maintains the user's travel budget while
    the travel plan is being developed.

    It does NOT:
        - search for hotels
        - search for flights
        - recommend destinations
        - make travel decisions
        - communicate directly with Gemini

    main.py is responsible for communicating between
    Budget and TravelAgent.
    """

    def __init__(self, total_budget, currency="CAD"):
        """
        Create a budget.

        Example:

            Budget(3000)

        means:

            Total budget = 3000 CAD
        """

        if total_budget is None:
            raise ValueError(
                "A budget amount is required."
            )

        try:
            total_budget = float(
                total_budget
            )

        except (TypeError, ValueError):
            raise ValueError(
                "Budget must be a valid number."
            )

        if total_budget < 0:
            raise ValueError(
                "Budget cannot be negative."
            )

        self.total_budget = total_budget

        self.currency = currency.upper()

        self.spent = 0.0

        self.remaining = total_budget

        self.expenses = []

    # ==========================================================
    # ADD EXPENSE
    # ==========================================================

    def add_expense(
        self,
        amount,
        category,
        description=""
    ):
        """
        Add an expense to the current trip budget.

        Example:

            budget.add_expense(
                800,
                "hotel",
                "5 nights"
            )
        """

        try:
            amount = float(
                amount
            )

        except (TypeError, ValueError):
            raise ValueError(
                "Expense amount must be a valid number."
            )

        if amount < 0:
            raise ValueError(
                "Expense cannot be negative."
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

        self.spent += amount

        self.remaining = (
            self.total_budget
            - self.spent
        )

    # ==========================================================
    # CHECK REMAINING
    # ==========================================================

    def get_remaining(self):
        """
        Return the amount of money remaining.
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
        Return the amount already spent.
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
        Return the original total budget.
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
        Return the current budget state.
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

            "expenses": self.expenses.copy()
        }

    # ==========================================================
    # CHECK WHETHER AN EXPENSE IS AFFORDABLE
    # ==========================================================

    def can_afford(self, amount):
        """
        Check whether an expense fits within the
        remaining budget.

        This does NOT add the expense.
        """

        try:
            amount = float(
                amount
            )

        except (TypeError, ValueError):
            return False

        if amount < 0:
            return False

        return amount <= self.remaining

    # ==========================================================
    # RESET
    # ==========================================================

    def reset(self):
        """
        Reset the budget to its original state.
        """

        self.spent = 0.0

        self.remaining = (
            self.total_budget
        )

        self.expenses = []