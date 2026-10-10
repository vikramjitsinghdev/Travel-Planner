"""Wanderlust's single orchestration layer. No workers or RecheckAgent."""
from ai.mood_agent import MoodAgent
from ai.travel_agent import TravelAgent
from ai.research_agent import ResearchAgent


class TravelPlanner:
    def __init__(self):
        self.mood_agent = MoodAgent()
        self.travel_agent = TravelAgent()
        self.research_agent = ResearchAgent()

    def run(self, user_input, trip_information=None):
        if not isinstance(user_input, str) or not user_input.strip():
            raise ValueError("Please describe what you want from your trip.")
        trip_information = trip_information or {}

        # 1. Understand the user's preferences using Groq.
        requirements = self.mood_agent.interpret(user_input, trip_information)

        # 2. Select exactly three destinations using Ollama GPT-OSS 20B Cloud.
        candidates = self.travel_agent.select_destinations(requirements, count=3)

        # 3. Deep research each selected destination using GPT-OSS 120B Cloud + Tavily.
        deep_result = self.research_agent.research_destinations(candidates, requirements)
        deep_by_key = {self._key(item): item for item in deep_result["destinations"]}

        # 4. Independent basic-info Tavily searches, plus Pexels and MapTiler enrichment.
        final_destinations = []
        verification = []
        for candidate in candidates:
            key = self._key(candidate)
            deep = deep_by_key.get(key, {})
            basic = self.travel_agent.get_basic_information(candidate["destination"], candidate["country"])
            comparison = self.travel_agent.compare_information(
                candidate["destination"], candidate["country"], deep, basic
            )

            # 5. If the two summaries conflict, rerun the Tavily research once using alternate queries.
            # No separate recheck agent and no worker fan-out.
            if not comparison.get("similar", False):
                retry_deep_result = self.research_agent.research_destinations([candidate], requirements, retry_number=1)
                retry_deep = retry_deep_result["destinations"][0]
                retry_comparison = self.travel_agent.compare_information(
                    candidate["destination"], candidate["country"], retry_deep, basic
                )
                deep = retry_deep
                comparison = {
                    **retry_comparison,
                    "retried": True,
                    "first_comparison": comparison,
                }
            else:
                comparison["retried"] = False

            enriched = self.travel_agent.enrich_destination(
                candidate["destination"], candidate["country"], basic
            )
            final_destinations.append({
                "destination": candidate["destination"],
                "name": candidate["destination"],
                "country": candidate["country"],
                "reason": candidate.get("reason", ""),
                "basic_info": basic.get("basic_info", ""),
                "key_facts": basic.get("key_facts", []),
                "images": enriched.get("images", []),
                "image_urls": enriched.get("image_urls", []),
                "map_coordinates": enriched.get("map_coordinates"),
                "map_url": enriched.get("map_url"),
                "research": deep,
                "research_result": deep,
                "major_attractions": deep.get("major_attractions", []),
                "cost_estimates": deep.get("cost_estimates", {}),
                "best_time_to_visit": deep.get("best_time_to_visit", ""),
                "local_transport": deep.get("local_transport", ""),
                "practical_tips": deep.get("practical_tips", []),
                "safety_and_accessibility_notes": deep.get("safety_and_accessibility_notes", []),
                "fit_to_user_preferences": deep.get("fit_to_user_preferences", ""),
                "uncertainties": deep.get("uncertainties", []),
                "source_urls": deep.get("source_urls", []),
                "basic_info_sources": basic.get("sources", []),
                "consistency_check": comparison,
                "enrichment_warnings": enriched.get("enrichment_warnings", []),
            })
            verification.append({
                "destination": candidate["destination"],
                "country": candidate["country"],
                **comparison,
            })

        return {
            "trip_requirements": requirements,
            "destinations": final_destinations,
            "verification": verification,
            "architecture": {
                "mood_model": "Groq GPT-OSS 20B",
                "destination_model": self.travel_agent.llm.model,
                "research_model": self.research_agent.llm.model,
                "workers_enabled": False,
                "recheck_agent_enabled": False,
            },
        }

    @staticmethod
    def _key(destination):
        return (
            str(destination.get("destination") or destination.get("name") or "").strip().casefold(),
            str(destination.get("country") or "").strip().casefold(),
        )


def run_travel_planner(user_input, trip_information=None):
    return TravelPlanner().run(user_input, trip_information)
