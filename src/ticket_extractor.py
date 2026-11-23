import json
import os
import re
from typing import Dict, Any, List

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI


load_dotenv()


class TicketExtractor:

    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-3.6-flash",
            temperature=0,
            google_api_key=os.environ["GEMINI_API_KEY"]
        )

    def _parse_response(
        self,
        response_text: str
    ) -> Dict[str, Any]:

        response_text = response_text.strip()

        if response_text.startswith("```"):
            response_text = re.sub(
                r"^```(?:json)?\s*",
                "",
                response_text
            )
            response_text = re.sub(
                r"\s*```$",
                "",
                response_text
            )

        try:
            data = json.loads(response_text)

        except json.JSONDecodeError:

            return {
                "customer": None,
                "order": None,
                "product": None,
                "issue": None,
                "evidence": None,
                "contact_details": None
            }

        fields = [
            "customer",
            "order",
            "product",
            "issue",
            "evidence",
            "contact_details"
        ]

        return {
            field: data.get(field)
            for field in fields
        }

    def extract(
        self,
        message: str,
        conversation_history: List[str] = None
    ) -> Dict[str, Any]:

        if conversation_history is None:
            conversation_history = []

        recent_history = conversation_history[-10:]

        history_text = "\n".join(
            recent_history
        )

        prompt = f"""
Extract support-ticket information from the current
customer message and the recent conversation history.

Use the conversation history to recover information that
the customer has already provided.

Return ONLY valid JSON.

Use exactly these fields:
- customer
- order
- product
- issue
- evidence
- contact_details

If a value is not available anywhere in the conversation,
return null.

Never invent or guess missing information.

RECENT CONVERSATION:
{history_text}

CURRENT CUSTOMER MESSAGE:
{message}
"""

        response = self.llm.invoke(prompt)

        if isinstance(response.content, str):

            response_text = response.content

        else:

            response_text = "".join(
                block.get("text", "")
                for block in response.content
                if isinstance(block, dict)
            )

        return self._parse_response(
            response_text
        )


if __name__ == "__main__":

    extractor = TicketExtractor()

    history = [
        """
        Hi, my name is John.
        My order ORD-12345 for the Premium Laptop
        was charged twice.
        I have an invoice showing both identical charges.
        You can contact me at john@example.com.
        """
    ]

    message = """
    I'm John again. My Premium Laptop was charged twice.
    Please help me resolve this.
    """

    ticket = extractor.extract(
        message=message,
        conversation_history=history
    )

    print(json.dumps(ticket, indent=2))