# budget.py

class BudgetManager:
    """
    Rough travel budget management system.

    Currently responsible for:
        - collecting budget information
        - storing expenses
        - calculating totals
        - calculating remaining budget
        - calculating daily budget
        - checking whether the user is over budget
        - displaying a budget summary

    This is intentionally a basic version.

    Later it can be connected to:
        - transportation APIs
        - hotel APIs
        - restaurant APIs
        - activity prices
        - destination recommendations
        - currency conversion
    """

    def __init__(self):

        # ------------------------------------------------------
        # Basic trip information
        # ------------------------------------------------------

        self.total_budget = 0.0

        self.number_of_travelers = 1

        self.trip_days = 1

        self.currency = "CAD"

        # ------------------------------------------------------
        # Budget categories
        # ------------------------------------------------------

        self.expenses = {
            "transportation": 0.0,
            "accommodation": 0.0,
            "food": 0.0,
            "activities": 0.0,
            "shopping": 0.0,
            "insurance": 0.0,
            "miscellaneous": 0.0,
            "emergency": 0.0,
        }

    # ==========================================================
    # INPUT METHODS
    # ==========================================================

    def set_total_budget(
        self,
        amount,
    ):
        """
        Set the total amount the user is willing to spend.
        """

        if amount < 0:
            raise ValueError(
                "Budget cannot be negative."
            )

        self.total_budget = float(
            amount
        )

    # ----------------------------------------------------------

    def set_number_of_travelers(
        self,
        number,
    ):
        """
        Set the number of people traveling.
        """

        if number < 1:
            raise ValueError(
                "There must be at least one traveler."
            )

        self.number_of_travelers = int(
            number
        )

    # ----------------------------------------------------------

    def set_trip_days(
        self,
        days,
    ):
        """
        Set the length of the trip.
        """

        if days < 1:
            raise ValueError(
                "Trip must be at least one day."
            )

        self.trip_days = int(
            days
        )

    # ----------------------------------------------------------

    def set_currency(
        self,
        currency,
    ):
        """
        Set the currency used by the planner.

        Example:
            CAD
            USD
            EUR
            JPY
        """

        currency = str(
            currency
        ).upper().strip()

        if not currency:
            raise ValueError(
                "Currency cannot be empty."
            )

        self.currency = currency

    # ==========================================================
    # EXPENSE MANAGEMENT
    # ==========================================================

    def set_expense(
        self,
        category,
        amount,
    ):
        """
        Set the total expense for a category.

        Example:

            set_expense(
                "food",
                500
            )
        """

        if category not in self.expenses:
            raise ValueError(
                f"Unknown budget category: "
                f"{category}"
            )

        if amount < 0:
            raise ValueError(
                "Expense cannot be negative."
            )

        self.expenses[category] = float(
            amount
        )

    # ----------------------------------------------------------

    def add_expense(
        self,
        category,
        amount,
    ):
        """
        Add money to an existing expense category.

        Example:

            add_expense(
                "food",
                50
            )

        If food was previously 300:

            food = 350
        """

        if category not in self.expenses:
            raise ValueError(
                f"Unknown budget category: "
                f"{category}"
            )

        if amount < 0:
            raise ValueError(
                "Expense cannot be negative."
            )

        self.expenses[category] += float(
            amount
        )

    # ----------------------------------------------------------

    def remove_expense(
        self,
        category,
        amount,
    ):
        """
        Remove an amount from an expense category.
        """

        if category not in self.expenses:
            raise ValueError(
                f"Unknown budget category: "
                f"{category}"
            )

        if amount < 0:
            raise ValueError(
                "Amount cannot be negative."
            )

        self.expenses[category] = max(
            0.0,
            self.expenses[category] - amount
        )

    # ==========================================================
    # CALCULATIONS
    # ==========================================================

    def get_total_expenses(
        self,
    ):
        """
        Return the total amount currently allocated/spent.
        """

        return sum(
            self.expenses.values()
        )

    # ----------------------------------------------------------

    def get_remaining_budget(
        self,
    ):
        """
        Return the amount remaining from the total budget.

        Can become negative if the user goes over budget.
        """

        return (
            self.total_budget
            - self.get_total_expenses()
        )

    # ----------------------------------------------------------

    def get_daily_budget(
        self,
    ):
        """
        Calculate the average available budget per day.

        This is based on the remaining budget.
        """

        if self.trip_days <= 0:
            return 0.0

        return (
            self.get_remaining_budget()
            / self.trip_days
        )

    # ----------------------------------------------------------

    def get_budget_per_person(
        self,
    ):
        """
        Calculate the total budget available per traveler.
        """

        if self.number_of_travelers <= 0:
            return 0.0

        return (
            self.total_budget
            / self.number_of_travelers
        )

    # ----------------------------------------------------------

    def get_expense_per_person(
        self,
    ):
        """
        Calculate current expenses per traveler.
        """

        if self.number_of_travelers <= 0:
            return 0.0

        return (
            self.get_total_expenses()
            / self.number_of_travelers
        )

    # ----------------------------------------------------------

    def get_daily_expense(
        self,
    ):
        """
        Calculate the current average spending per day.
        """

        if self.trip_days <= 0:
            return 0.0

        return (
            self.get_total_expenses()
            / self.trip_days
        )

    # ==========================================================
    # BUDGET STATUS
    # ==========================================================

    def is_over_budget(
        self,
    ):
        """
        Returns True if expenses exceed the budget.
        """

        return (
            self.get_total_expenses()
            > self.total_budget
        )

    # ----------------------------------------------------------

    def get_budget_status(
        self,
    ):
        """
        Returns a simple status.

        Possible results:

            UNDER
            EXACT
            OVER
        """

        remaining = (
            self.get_remaining_budget()
        )

        if remaining > 0:
            return "UNDER"

        if remaining == 0:
            return "EXACT"

        return "OVER"

    # ==========================================================
    # CATEGORY ANALYSIS
    # ==========================================================

    def get_category_percentage(
        self,
        category,
    ):
        """
        Return what percentage of the current budget is being
        used by a particular category.
        """

        if category not in self.expenses:
            raise ValueError(
                f"Unknown budget category: "
                f"{category}"
            )

        if self.total_budget <= 0:
            return 0.0

        return (
            self.expenses[category]
            / self.total_budget
        ) * 100

    # ----------------------------------------------------------

    def get_category_breakdown(
        self,
    ):
        """
        Return every category and its percentage of the budget.
        """

        breakdown = {}

        for category in self.expenses:

            breakdown[category] = {
                "amount": self.expenses[
                    category
                ],
                "percentage": (
                    self.get_category_percentage(
                        category
                    )
                ),
            }

        return breakdown

    # ==========================================================
    # VALIDATION
    # ==========================================================

    def validate_budget(
        self,
    ):
        """
        Performs basic validation.

        Returns True if the basic budget information is valid.
        """

        if self.total_budget < 0:
            return False

        if self.number_of_travelers < 1:
            return False

        if self.trip_days < 1:
            return False

        for amount in self.expenses.values():

            if amount < 0:
                return False

        return True

    # ==========================================================
    # RESET
    # ==========================================================

    def reset_budget(
        self,
    ):
        """
        Reset the entire budget.
        """

        self.total_budget = 0.0

        self.number_of_travelers = 1

        self.trip_days = 1

        self.currency = "CAD"

        for category in self.expenses:

            self.expenses[category] = 0.0

    # ==========================================================
    # SUMMARY
    # ==========================================================

    def get_summary(
        self,
    ):
        """
        Return all important budget information as a
        dictionary.

        This will eventually be useful for the web frontend.
        """

        return {
            "currency": self.currency,

            "total_budget": self.total_budget,

            "travelers": (
                self.number_of_travelers
            ),

            "trip_days": self.trip_days,

            "total_expenses": (
                self.get_total_expenses()
            ),

            "remaining": (
                self.get_remaining_budget()
            ),

            "daily_budget": (
                self.get_daily_budget()
            ),

            "budget_per_person": (
                self.get_budget_per_person()
            ),

            "expense_per_person": (
                self.get_expense_per_person()
            ),

            "daily_expense": (
                self.get_daily_expense()
            ),

            "status": (
                self.get_budget_status()
            ),

            "expenses": self.expenses.copy(),
        }

    # ==========================================================
    # DISPLAY
    # ==========================================================

    def display_summary(
        self,
    ):
        """
        Print a readable budget summary.
        """

        summary = self.get_summary()

        print(
            "\n=============================="
        )

        print(
            "       TRAVEL BUDGET"
        )

        print(
            "=============================="
        )

        print(
            f"Currency: "
            f"{summary['currency']}"
        )

        print(
            f"Travelers: "
            f"{summary['travelers']}"
        )

        print(
            f"Trip length: "
            f"{summary['trip_days']} days"
        )

        print(
            f"Total budget: "
            f"{summary['total_budget']:.2f}"
        )

        print(
            f"Total expenses: "
            f"{summary['total_expenses']:.2f}"
        )

        print(
            f"Remaining: "
            f"{summary['remaining']:.2f}"
        )

        print(
            f"Daily budget: "
            f"{summary['daily_budget']:.2f}"
        )

        print(
            f"Budget per person: "
            f"{summary['budget_per_person']:.2f}"
        )

        print(
            f"Status: "
            f"{summary['status']}"
        )

        print(
            "\nExpense Breakdown:"
        )

        print(
            "------------------------------"
        )

        for category, amount in (
            summary["expenses"].items()
        ):

            percentage = (
                self.get_category_percentage(
                    category
                )
            )

            print(
                f"{category:<18}"
                f"{amount:>8.2f} "
                f"({percentage:>5.1f}%)"
            )