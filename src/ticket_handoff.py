from typing import Dict, Any
import re


class TicketHandoff:

    def _mask_email(self, email: str) -> str:

        if "@" not in email:
            return email

        username, domain = email.split("@", 1)

        if len(username) <= 2:
            masked_username = "*" * len(username)
        else:
            masked_username = (
                username[0]
                + "*" * (len(username) - 2)
                + username[-1]
            )

        return masked_username + "@" + domain

    def _mask_phone(self, phone: str) -> str:

        digits = re.sub(r"\D", "", phone)

        if len(digits) <= 4:
            return "*" * len(digits)

        return "*" * (len(digits) - 4) + digits[-4:]

    def _mask_sensitive_text(self, text: str) -> str:

        if not text:
            return text

        text = str(text)

        email_pattern = (
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\."
            r"[A-Za-z]{2,}\b"
        )

        text = re.sub(
            email_pattern,
            lambda match: self._mask_email(match.group()),
            text
        )

        phone_pattern = r"\+?\d[\d\s().-]{7,}\d"

        text = re.sub(
            phone_pattern,
            lambda match: self._mask_phone(match.group()),
            text
        )

        return text

    def create_summary(
        self,
        ticket: Dict[str, Any]
    ) -> Dict[str, Any]:

        summary = {
            "customer": self._mask_sensitive_text(
                ticket.get("customer")
            ),
            "order": ticket.get("order"),
            "product": ticket.get("product"),
            "issue": self._mask_sensitive_text(
                ticket.get("issue")
            ),
            "evidence": self._mask_sensitive_text(
                ticket.get("evidence")
            ),
            "contact_details": self._mask_sensitive_text(
                ticket.get("contact_details")
            ),
            "priority": ticket.get("priority"),
            "status": ticket.get("status", "open")
        }

        return summary


if __name__ == "__main__":

    handoff = TicketHandoff()

    ticket = {
        "customer": "John",
        "order": "ORD-12345",
        "product": "Premium Laptop",
        "issue": "Customer was charged twice.",
        "evidence": "Invoice confirms two identical charges.",
        "contact_details": "john@example.com",
        "priority": "high",
        "status": "escalated"
    }

    result = handoff.create_summary(ticket)

    print(result)