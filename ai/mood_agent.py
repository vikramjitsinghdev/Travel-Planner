import json
import os

from dotenv import load_dotenv
from groq import Groq

from mood.mood_keywords import MoodKeywords
from mood.mood_score import MoodScore


class MoodAgent:
    """
    AI-powered travel preference interpreter.

    Responsibilities:

        1. Groq understands the user's natural language.
        2. Groq determines whether preferences are wanted
           or avoided.
        3. MoodKeywords normalizes those preferences into
           the application's canonical vocabulary.
        4. MoodScore assigns deterministic numerical scores.

    IMPORTANT:

        Groq is the authority for CONTEXT.

        MoodKeywords is only a vocabulary/normalization helper.

        MoodScore is only responsible for numerical scoring.

    This class does NOT recommend destinations.
    """

    def __init__(self):

        load_dotenv()

        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError(
                "GROQ_API_KEY is not set in the .env file."
            )

        self.client = Groq(
            api_key=api_key
        )

        self.model = "openai/gpt-oss-20b"

        self.mood_keywords = MoodKeywords()

        self.mood_score = MoodScore()

    # ==========================================================
    # MAIN INTERPRETATION
    # ==========================================================

    def interpret(self, user_input):
        """
        Interpret the user's travel request.

        Flow:

            User input
                ↓
            Groq
                ↓
            Raw preferences
                ↓
            Canonical moods
                ↓
            Mood scores
                ↓
            Return to main.py
        """

        if not isinstance(user_input, str):
            raise TypeError(
                "user_input must be a string."
            )

        user_input = user_input.strip()

        if not user_input:
            raise ValueError(
                "user_input cannot be empty."
            )

        # ------------------------------------------------------
        # 1. Ask Groq to understand the user's language.
        # ------------------------------------------------------

        response = self.client.chat.completions.create(

            model=self.model,

            messages=[
                {
                    "role": "system",

                    "content": """
You are a travel preference interpretation AI.

Your ONLY job is to understand the user's travel
preferences.

You must identify:

1. wanted:
   Things the user wants, likes, prefers, or is
   interested in.

2. avoid:
   Things the user does not want, dislikes, wants
   to escape, wants to stay away from, or wants
   to minimize.

3. summary:
   A concise description of the user's overall
   travel preferences.

IMPORTANT CONTEXT RULES:

You MUST understand the meaning of the entire sentence,
not just individual keywords.

Examples:

"I want to escape the city."
→ avoid: ["urban"]

"I want to get away from crowded cities."
→ avoid: ["crowded", "urban"]

"I don't want nightlife."
→ avoid: ["nightlife"]

"I love exploring cities."
→ wanted: ["urban"]

"I want a city with beautiful architecture."
→ wanted: ["urban", "architecture"]

"I want mountains instead of cities."
→ wanted: ["mountains"]
→ avoid: ["urban"]

"I want peace and quiet."
→ wanted: ["peaceful", "quiet"]

"I want nature but I don't want crowded places."
→ wanted: ["nature"]
→ avoid: ["crowded"]

DO NOT classify a concept as wanted simply because
its keyword appears in the user's sentence.

For example:

"I want to escape the city."

must NOT produce:

wanted: ["urban"]

The meaning is that the user wants to avoid urban
environments.

Another example:

"I don't want crowded cities."

must NOT produce:

wanted: ["urban", "crowded"]

They are both unwanted.

IMPORTANT:

- Understand negation.
- Understand "avoid", "escape", "away from",
  "instead of", "without", "don't want", "do not want",
  "hate", "dislike", and similar expressions.
- Do not recommend destinations.
- Do not calculate numerical scores.
- Do not invent preferences.
- Do not assume a preference merely because it is
  associated with another preference.
- Keep the raw preferences concise.
- Preserve the user's actual meaning.

Return ONLY valid JSON using the required schema.
"""
                },

                {
                    "role": "user",
                    "content": user_input
                }
            ],

            response_format={
                "type": "json_schema",

                "json_schema": {
                    "name": "travel_preferences",

                    "strict": True,

                    "schema": {
                        "type": "object",

                        "properties": {

                            "wanted": {
                                "type": "array",

                                "items": {
                                    "type": "string"
                                }
                            },

                            "avoid": {
                                "type": "array",

                                "items": {
                                    "type": "string"
                                }
                            },

                            "summary": {
                                "type": "string"
                            }
                        },

                        "required": [
                            "wanted",
                            "avoid",
                            "summary"
                        ],

                        "additionalProperties": False
                    }
                }
            }
        )

        # ------------------------------------------------------
        # 2. Convert Groq's response into Python.
        # ------------------------------------------------------

        raw_result = json.loads(
            response.choices[0].message.content
        )

        raw_wanted = raw_result.get(
            "wanted",
            []
        )

        raw_avoid = raw_result.get(
            "avoid",
            []
        )

        # ------------------------------------------------------
        # 3. Normalize Groq's interpretation.
        #
        # IMPORTANT:
        #
        # We use MoodKeywords to normalize the concepts
        # Groq already classified.
        #
        # We do NOT independently classify the entire
        # user input and then merge it blindly.
        #
        # This prevents:
        #
        # "escape the city"
        #
        # from becoming:
        #
        # wanted = ["urban"]
        # ------------------------------------------------------

        wanted = self._normalize_ai_moods(
            raw_wanted
        )

        avoid = self._normalize_ai_moods(
            raw_avoid
        )

        # ------------------------------------------------------
        # 4. Remove conflicts.
        #
        # If Groq somehow places the same canonical mood
        # in both wanted and avoid, avoid takes priority.
        # ------------------------------------------------------

        wanted = [
            mood
            for mood in wanted
            if mood not in avoid
        ]

        # ------------------------------------------------------
        # 5. Calculate deterministic scores.
        # ------------------------------------------------------

        canonical_profile = {
            "wanted": wanted,
            "avoid": avoid
        }

        score_analysis = (
            self.mood_score.analyze_profile(
                canonical_profile
            )
        )

        # ------------------------------------------------------
        # 6. Return everything to main.py.
        # ------------------------------------------------------

        return {
            "wanted": wanted,

            "avoid": avoid,

            "scores": score_analysis["combined"],

            "score_details": score_analysis,

            "summary": raw_result.get(
                "summary",
                ""
            ),

            "raw_wanted": raw_wanted,

            "raw_avoid": raw_avoid
        }

    # ==========================================================
    # NORMALIZE AI PREFERENCES
    # ==========================================================

    def _normalize_ai_moods(self, ai_moods):
        """
        Convert Groq's natural-language preference phrases
        into canonical application moods.

        IMPORTANT:

        This function does NOT decide whether something is
        wanted or avoided.

        Groq has already made that decision.

        Example:

            "peaceful"
                ↓
            quiet

            "beautiful nature"
                ↓
            nature

            "crowded cities"
                ↓
            crowded + urban
        """

        if not isinstance(ai_moods, list):
            return []

        normalized_moods = []

        for phrase in ai_moods:

            if not isinstance(
                phrase,
                str
            ):
                continue

            phrase = (
                self.mood_keywords.normalize(
                    phrase
                )
            )

            if not phrase:
                continue

            # --------------------------------------------------
            # First check if Groq directly returned a canonical
            # mood.
            # --------------------------------------------------

            if self.mood_keywords.is_valid_mood(
                phrase
            ):

                if phrase not in normalized_moods:

                    normalized_moods.append(
                        phrase
                    )

                continue

            # --------------------------------------------------
            # Otherwise try to map the phrase to the
            # application's vocabulary.
            # --------------------------------------------------

            matches = (
                self._find_canonical_matches(
                    phrase
                )
            )

            for mood in matches:

                if mood not in normalized_moods:

                    normalized_moods.append(
                        mood
                    )

        return normalized_moods

    # ==========================================================
    # FIND CANONICAL MATCHES
    # ==========================================================

    def _find_canonical_matches(self, phrase):
        """
        Find canonical moods represented by an AI-generated
        phrase.

        This is deliberately conservative.

        We do NOT search the original user input here.

        We search only the specific phrase that Groq has
        already classified as wanted or avoided.
        """

        matches = []

        # ------------------------------------------------------
        # First use the MoodKeywords vocabulary.
        # ------------------------------------------------------

        keyword_matches = (
            self.mood_keywords.find_moods(
                phrase
            )
        )

        for mood in keyword_matches:

            if mood not in matches:

                matches.append(
                    mood
                )

        # ------------------------------------------------------
        # Handle common semantic mappings.
        #
        # These are mappings between language and your
        # canonical vocabulary, not contextual decisions.
        # ------------------------------------------------------

        semantic_mappings = {

            "peaceful": [
                "quiet"
            ],

            "peace": [
                "quiet"
            ],

            "tranquil": [
                "quiet"
            ],

            "tranquility": [
                "quiet"
            ],

            "serene": [
                "quiet"
            ],

            "serenity": [
                "quiet"
            ],

            "relaxing": [
                "relaxation"
            ],

            "relaxed": [
                "relaxation"
            ],

            "relax": [
                "relaxation"
            ],

            "natural": [
                "nature"
            ],

            "beautiful nature": [
                "nature"
            ],

            "scenic nature": [
                "nature"
            ],

            "mountainous": [
                "mountains"
            ],

            "mountain": [
                "mountains"
            ],

            "hiking trails": [
                "hiking"
            ],

            "trekking": [
                "hiking"
            ],

            "city": [
                "urban"
            ],

            "cities": [
                "urban"
            ],

            "urban areas": [
                "urban"
            ],

            "urban environments": [
                "urban"
            ],

            "busy cities": [
                "urban",
                "crowded"
            ],

            "crowded cities": [
                "urban",
                "crowded"
            ],

            "crowded areas": [
                "crowded"
            ],

            "crowded places": [
                "crowded"
            ],

            "crowded tourist areas": [
                "crowded"
            ],

            "night life": [
                "nightlife"
            ]
        }

        if phrase in semantic_mappings:

            for mood in semantic_mappings[phrase]:

                if mood not in matches:

                    matches.append(
                        mood
                    )

        return matches