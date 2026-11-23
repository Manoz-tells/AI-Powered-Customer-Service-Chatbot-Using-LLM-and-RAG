from typing import Dict
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

from llm_safe_invoke import safe_llm_invoke


load_dotenv()


class ToneAdjuster:

    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-3.6-flash"
        )

    def adjust(
        self,
        response: str,
        sentiment: str,
        confidence: float
    ) -> str:

        if confidence < 0.70:
            tone_instruction = """
Keep the response neutral, professional, and clear.
Do not make assumptions about the customer's emotional state.
"""

        elif sentiment == "positive":
            tone_instruction = """
Use a friendly, positive, and appreciative tone.
"""

        elif sentiment == "negative":
            tone_instruction = """
Use a calm, empathetic, and professional tone.
Acknowledge the customer's concern without changing the
information or business policy in the original response.
"""

        elif sentiment == "frustrated":
            tone_instruction = """
Use a calm, empathetic, reassuring, and professional tone.
Acknowledge the customer's frustration and focus on helping.
Do not blame the customer.
Do not change the information or business policy in the
original response.
"""

        elif sentiment == "urgent":
            tone_instruction = """
Use a calm, direct, and reassuring tone.
Prioritize clarity and immediate next steps.
Do not make promises that are not present in the original response.
Do not change business policy.
"""

        elif sentiment == "sarcastic":
            tone_instruction = """
Use a calm, respectful, and empathetic tone.
Do not respond sarcastically or mirror the customer's sarcasm.
Acknowledge the underlying concern and remain professional.
Do not change the information or business policy in the
original response.
"""

        else:
            tone_instruction = """
Use a neutral, professional, and helpful tone.
"""

        prompt = f"""
You are a customer service response tone adjuster.

Your task is ONLY to adjust the tone of the response.

IMPORTANT:
- Preserve the factual information.
- Preserve the business policy.
- Do not add new promises.
- Do not invent information.
- Do not remove important information.
- Do not change prices, refunds, deadlines, eligibility,
  procedures, or other business rules.
- Only improve the tone and wording.

Customer sentiment:
{sentiment}

Sentiment confidence:
{confidence}

Tone instruction:
{tone_instruction}

Original response:
{response}

Return ONLY the revised customer-service response.
"""

        fallback_response = response

        adjusted_text, fallback_used = safe_llm_invoke(
            invoke_function=lambda: self.llm.invoke(prompt),
            fallback_response=fallback_response
        )

        if fallback_used:
            print(
                "[ToneAdjuster] Gemini unavailable. "
                "Using original response without tone adjustment."
            )

        return adjusted_text.strip()


if __name__ == "__main__":

    adjuster = ToneAdjuster()

    original_response = (
        "Your payment was charged twice. "
        "The duplicate charge will be reviewed by the support team."
    )

    adjusted_response = adjuster.adjust(
        response=original_response,
        sentiment="urgent",
        confidence=0.98
    )

    print("\nOriginal response:")
    print(original_response)

    print("\nAdjusted response:")
    print(adjusted_response)