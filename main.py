from dataclasses import dataclass
from typing import List
# ============================================================
# DATA STRUCTURES
# ============================================================
@dataclass
class UserPreferences:
    mood: dict
    budget: float
    duration_days: int
    food_preferences: List[str]
    preferred_transport: List[str]
    flexible_transport: bool
@dataclass
class Destination:
    name: str
    country: str
    # Experience scores: 0-1
    nature: float
    adventure: float
    relaxation: float
    culture: float
    nightlife: float
    food: float
    luxury: float
    # Available transportation
    transport: dict
@dataclass
class TransportOption:
    transport_type: str
    cost: float
    duration_hours: float
    experience_score: float
    comfort_score: float
# ============================================================
# DESTINATION DATABASE
# ============================================================
destinations = [
    Destination(
        name="Banff",
        country="Canada",
        nature=0.98,
        adventure=0.95,
        relaxation=0.80,
        culture=0.45,
        nightlife=0.25,
        food=0.70,
        luxury=0.55,
        transport={
            "air": True,
            "road": True,
            "train": True,
            "water": False
        }
    ),
    Destination(
        name="Vancouver",
        country="Canada",
        nature=0.85,
        adventure=0.75,
        relaxation=0.70,
        culture=0.90,
        nightlife=0.85,
        food=0.95,
        luxury=0.80,
        transport={
            "air": True,
            "road": True,
            "train": True,
            "water": True
        }
    ),
    Destination(
        name="Tokyo",
        country="Japan",
        nature=0.55,
        adventure=0.70,
        relaxation=0.45,
        culture=0.98,
        nightlife=0.95,
        food=0.99,
        luxury=0.90,

        transport={
            "air": True,
            "road": True,
            "train": True,
            "water": True
        }
    )
]
# ============================================================
# USER INPUT
# ============================================================
def get_user_preferences():
    print("\n===== TRAVEL PLANNER =====\n")
    budget = float(input("Travel budget ($): "))
    duration = int(input("Trip duration (days): "))
    print("\nChoose your moods.")
    mood = {
        "nature": float(input("Nature (0-1): ")),
        "adventure": float(input("Adventure (0-1): ")),
        "relaxation": float(input("Relaxation (0-1): ")),
        "culture": float(input("Culture (0-1): ")),
        "nightlife": float(input("Nightlife (0-1): ")),
        "food": float(input("Food (0-1): ")),
        "luxury": float(input("Luxury (0-1): "))
    }
    food = input("\nFood preferences (comma separated): ").split(",")
    print("\nTransportation preferences:")
    print("1. Air")
    print("2. Road")
    print("3. Train")
    print("4. Water")
    transport_input = input(
        "Enter choices separated by commas: "
    )
    transport_map = {
        "1": "air",
        "2": "road",
        "3": "train",
        "4": "water"
    }
    preferred_transport = []
    for choice in transport_input.split(","):
        choice = choice.strip()
        if choice in transport_map:
            preferred_transport.append(
                transport_map[choice]
            )
    flexible = input("\nAre you willing to use other transportation "
        "if it provides a better experience? (y/n): ").lower() == "y"
    return UserPreferences(
        mood=mood,
        budget=budget,
        duration_days=duration,
        food_preferences=food,
        preferred_transport=preferred_transport,
        flexible_transport=flexible
    )
# ============================================================
# MOOD MATCHING
# ============================================================
def calculate_mood_match(user, destination):
    destination_scores = {
        "nature": destination.nature,
        "adventure": destination.adventure,
        "relaxation": destination.relaxation,
        "culture": destination.culture,
        "nightlife": destination.nightlife,
        "food": destination.food,
        "luxury": destination.luxury
    }
    total_score = 0
    total_weight = 0
    for mood, importance in user.mood.items():
        destination_score = destination_scores[mood]
        total_score += (importance * destination_score)
        total_weight += importance
    if total_weight == 0:
        return 0
    return total_score / total_weight
# ============================================================
# TRANSPORTATION SCORING
# ============================================================
def calculate_transport_score(user,destination):
    available = destination.transport
    if not available:
        return 0
    score = 0
    for transport in user.preferred_transport:
        if available.get(transport, False):
            score += 1
    if len(user.preferred_transport) == 0:
        return 0.5
    score /= len(user.preferred_transport)
    return score
# ==========================================================
# DESTINATION RANKING
# ============================================================
def rank_destinations(user):
    results = []
    for destination in destinations:
        mood_score = calculate_mood_match(user,destination)
        transport_score = calculate_transport_score(user,destination)
        # Initial weighting
        overall_score = (
            mood_score * 0.75 +
            transport_score * 0.25
        )
        results.append({
            "destination": destination,
            "mood_score": mood_score,
            "transport_score": transport_score,
            "overall_score": overall_score
        })
    results.sort(
        key=lambda x: x["overall_score"],
        reverse=True
    )
    return results
# ============================================================
# TRANSPORTATION OPTIONS
# ============================================================
def generate_transport_options(destination):
    # TEMPORARY DATA
    # Eventually these values come from APIs.
    options = []
    if destination.transport.get("air"):
        options.append(
            TransportOption(
                transport_type="air",
                cost=500,
                duration_hours=3,
                experience_score=0.60,
                comfort_score=0.80
            )
        )
    if destination.transport.get("train"):
        options.append(
            TransportOption(
                transport_type="train",
                cost=250,
                duration_hours=8,
                experience_score=0.85,
                comfort_score=0.90
            )
        )
    if destination.transport.get("road"):
        options.append(
            TransportOption(
                transport_type="road",
                cost=150,
                duration_hours=10,
                experience_score=0.90,
                comfort_score=0.60
            )
        )
    if destination.transport.get("water"):
        options.append(
            TransportOption(
                transport_type="water",
                cost=300,
                duration_hours=12,
                experience_score=0.95,
                comfort_score=0.75
            )
        )
    return options
# ============================================================
# TRANSPORTATION COMPARISON
# ============================================================
def compare_transport(options):
    print("\n===== TRANSPORTATION COMPARISON =====")
    for option in options:
        print(f"\n{option.transport_type.upper()}")
        print(f"Cost: ${option.cost}")
        print(f"Duration: {option.duration_hours} hours")
        print(f"Experience: "
            f"{option.experience_score:.2f}")
        print(f"Comfort: "
            f"{option.comfort_score:.2f}")
# ============================================================
# BASIC TRAVEL PLAN
# ============================================================
def create_basic_plan(
    user,
    destination,
    transport_options
):
    remaining_budget = user.budget
    # Sort transportation by experience
    transport_options.sort(
        key=lambda x: x.experience_score,
        reverse=True
    )
    plan = []
    # VERY SIMPLE FIRST VERSION
    # Later this becomes an optimization problem.
    for option in transport_options:
        if option.cost <= remaining_budget:
            plan.append(option)
            remaining_budget -= option.cost
    return plan, remaining_budget
# ============================================================
# OUTPUT
# ============================================================
def display_results(
    user,
    ranked_destinations
):
    print("\n\n===================================")
    print("       RECOMMENDED DESTINATIONS")
    print("===================================\n")
    for index, result in enumerate(
        ranked_destinations,
        start=1
    ):
        destination = result["destination"]
        print(
            f"{index}. "
            f"{destination.name}, "
            f"{destination.country}"
        )
        print(
            f"   Mood Match: "
            f"{result['mood_score']:.2%}"
        )
        print(
            f"   Transport Match: "
            f"{result['transport_score']:.2%}"
        )
        print(
            f"   Overall Score: "
            f"{result['overall_score']:.2%}"
        )
        print()
# ============================================================
# MAIN PROGRAM
# ============================================================
def main():
    user = get_user_preferences()
    ranked = rank_destinations(user)
    display_results(
        user,
        ranked
    )
    best_destination = (
        ranked[0]["destination"]
    )
    print(
        "\n==================================="
    )
    print(
        f"BEST DESTINATION: "
        f"{best_destination.name}"
    )
    print(
        "==================================="
    )
    transport_options = (
        generate_transport_options(
            best_destination
        )
    )
    compare_transport(transport_options)
    plan, remaining = create_basic_plan(
        user,
        best_destination,
        transport_options
    )
    print(
        "\n===== BASIC TRAVEL PLAN ====="
    )
    for option in plan:
        print(
            f"- {option.transport_type.upper()} "
            f"${option.cost}"
        )
    print(
        f"\nRemaining budget: "
        f"${remaining:.2f}"
    )
if __name__ == "__main__":
    main()