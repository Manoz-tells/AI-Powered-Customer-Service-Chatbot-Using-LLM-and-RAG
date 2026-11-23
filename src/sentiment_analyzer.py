from typing import Dict, Any, List

from langchain_google_genai import ChatGoogleGenerativeAI

from dotenv import load_dotenv

import json
import re


load_dotenv()


class SentimentAnalyzer:

    def __init__(self):

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-3.6-flash"
        )

    # ========================================================
    # LOCAL FALLBACK SENTIMENT ANALYSIS
    # ========================================================

    def _fallback_analyze(
        self,
        message: str,
        conversation_history: List[str] = None
    ) -> Dict[str, Any]:

        text = message.lower()

        history_text = " ".join(
            conversation_history[-10:]
            if conversation_history
            else []
        ).lower()

        combined_text = (
            history_text + " " + text
        )

        # ----------------------------------------------------
        # URGENT
        # ----------------------------------------------------

        urgent_patterns = [
            r"\burgent\b",
            r"\basap\b",
            r"\bimmediately\b",
            r"\bimmediate\b",
            r"\bemergency\b",
            r"\bright now\b",
            r"\bcritical\b",
            r"\btime[- ]critical\b"
        ]

        if any(
            re.search(pattern, text)
            for pattern in urgent_patterns
        ):

            return {
                "sentiment": "urgent",
                "confidence": 0.90,
                "reason": (
                    "The message contains language "
                    "indicating an urgent issue."
                )
            }

        # ----------------------------------------------------
        # SARCASM
        # ----------------------------------------------------

        sarcastic_patterns = [
            r"yeah right",
            r"great job",
            r"thanks for nothing",
            r"what a surprise",
            r"brilliant",
            r"nice job",
            r"wow.*great"
        ]

        if any(
            re.search(pattern, text)
            for pattern in sarcastic_patterns
        ):

            return {
                "sentiment": "sarcastic",
                "confidence": 0.80,
                "reason": (
                    "The message contains wording "
                    "that may indicate sarcasm."
                )
            }

        # ----------------------------------------------------
        # FRUSTRATED
        # ----------------------------------------------------

        frustrated_patterns = [
            r"\bfrustrat",
            r"\bangry\b",
            r"\bannoyed\b",
            r"\bridiculous\b",
            r"\bterrible\b",
            r"\bworst\b",
            r"\buseless\b",
            r"\bnobody\b",
            r"\bno one\b",
            r"\bstill not\b",
            r"\bstill hasn't\b",
            r"\bnot fixed\b",
            r"\bhow many times\b",
            r"\balready contacted\b"
        ]

        if any(
            re.search(pattern, combined_text)
            for pattern in frustrated_patterns
        ):

            return {
                "sentiment": "frustrated",
                "confidence": 0.85,
                "reason": (
                    "The message or recent conversation "
                    "indicates repeated dissatisfaction."
                )
            }

        # ----------------------------------------------------
        # NEGATIVE
        # ----------------------------------------------------

        negative_patterns = [
            r"\bproblem\b",
            r"\bissue\b",
            r"\bwrong\b",
            r"\bfailed\b",
            r"\bfailure\b",
            r"\bnot working\b",
            r"\bcancel\b",
            r"\bcomplaint\b",
            r"\bdisappointed\b",
            r"\bunauthorized\b",
            r"\bcharged twice\b",
            r"\bcharged again\b"
        ]

        if any(
            re.search(pattern, combined_text)
            for pattern in negative_patterns
        ):

            return {
                "sentiment": "negative",
                "confidence": 0.80,
                "reason": (
                    "The message indicates a problem "
                    "or dissatisfaction."
                )
            }

        # ----------------------------------------------------
        # POSITIVE
        # ----------------------------------------------------

        positive_patterns = [
            r"\bthank you\b",
            r"\bthanks\b",
            r"\bgreat\b",
            r"\bexcellent\b",
            r"\bperfect\b",
            r"\bawesome\b",
            r"\bhelpful\b",
            r"\bappreciate\b",
            r"\bgood job\b"
        ]

        if any(
            re.search(pattern, text)
            for pattern in positive_patterns
        ):

            return {
                "sentiment": "positive",
                "confidence": 0.85,
                "reason": (
                    "The message contains positive "
                    "or appreciative language."
                )
            }

        # ----------------------------------------------------
        # NEUTRAL
        # ----------------------------------------------------

        return {
            "sentiment": "neutral",
            "confidence": 0.75,
            "reason": (
                "No strong emotional or urgent "
                "language was detected."
            )
        }

    # ========================================================
    # MAIN ANALYSIS
    # ========================================================

    def analyze(
        self,
        message: str,
        conversation_history: List[str] = None
    ) -> Dict[str, Any]:

        if conversation_history is None:
            conversation_history = []

        # Only use the most recent 10 messages.
        recent_history = conversation_history[-10:]

        history_text = "\n".join(
            f"Message {i + 1}: {msg}"
            for i, msg in enumerate(recent_history)
        )

        if not history_text:
            history_text = "No previous conversation."

        prompt = f"""
You are a customer service sentiment classifier.

Analyze the customer's CURRENT message together with the recent
CONVERSATION HISTORY.

Classify the overall customer state into EXACTLY ONE category:

positive
neutral
negative
frustrated
urgent
sarcastic

Return ONLY valid JSON in this exact format:

{{
    "sentiment": "category",
    "confidence": 0.0,
    "reason": "short explanation"
}}

Rules:

- confidence must be between 0.0 and 1.0
- urgent means the customer indicates an immediate or time-critical problem
- frustrated means clear anger, repeated complaints, or strong dissatisfaction
- sarcastic means criticism expressed through irony or sarcastic wording
- Consider repeated complaints in the conversation history.
- A calm current message can still indicate an unresolved negative situation
  when the history clearly shows continuing problems.
- Do not invent information.

CONVERSATION HISTORY:

{history_text}

CURRENT MESSAGE:

{message}
"""

        try:

            response = self.llm.invoke(
                prompt
            )

            text = response.content

            if isinstance(text, list):

                text = "".join(
                    block.get("text", "")
                    for block in text
                    if isinstance(block, dict)
                )

            text = text.strip()

            if text.startswith("```"):

                text = text.replace(
                    "```json",
                    ""
                )

                text = text.replace(
                    "```",
                    ""
                )

                text = text.strip()

            result = json.loads(text)

            sentiment = result.get(
                "sentiment",
                "neutral"
            )

            confidence = float(
                result.get(
                    "confidence",
                    0.0
                )
            )

            reason = result.get(
                "reason",
                ""
            )

            valid_sentiments = {
                "positive",
                "neutral",
                "negative",
                "frustrated",
                "urgent",
                "sarcastic"
            }

            if sentiment not in valid_sentiments:

                sentiment = "neutral"

            confidence = max(
                0.0,
                min(
                    1.0,
                    confidence
                )
            )

            return {
                "sentiment": sentiment,
                "confidence": confidence,
                "reason": reason,
                "fallback": False
            }

        # ====================================================
        # GEMINI FAILURE
        # ====================================================

        except Exception as error:

            error_text = str(
                error
            ).lower()

            if (
                "429" in error_text
                or "resource_exhausted" in error_text
                or "quota" in error_text
                or "503" in error_text
                or "unavailable" in error_text
            ):

                fallback_result = (
                    self._fallback_analyze(
                        message=message,
                        conversation_history=(
                            conversation_history
                        )
                    )
                )

                fallback_result["fallback"] = True

                fallback_result["error"] = (
                    "Gemini service temporarily unavailable."
                )

                return fallback_result

            # ------------------------------------------------
            # Invalid Gemini JSON
            # ------------------------------------------------

            if (
                isinstance(
                    error,
                    (
                        json.JSONDecodeError,
                        ValueError,
                        TypeError
                    )
                )
            ):

                fallback_result = (
                    self._fallback_analyze(
                        message=message,
                        conversation_history=(
                            conversation_history
                        )
                    )
                )

                fallback_result["fallback"] = True

                return fallback_result

            # ------------------------------------------------
            # Unexpected error
            # ------------------------------------------------

            raise


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    analyzer = SentimentAnalyzer()

    history = [
        "My payment was charged twice.",
        "I already contacted support about this.",
        "Nobody has fixed the duplicate payment.",
        "I have been waiting for a solution."
    ]

    current_message = (
        "Can you please check it again?"
    )

    result = analyzer.analyze(
        current_message,
        history
    )

    print(
        json.dumps(
            result,
            indent=2
        )
    )