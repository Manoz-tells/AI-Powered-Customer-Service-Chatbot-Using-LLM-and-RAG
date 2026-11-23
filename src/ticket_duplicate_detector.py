from typing import Dict, Any, List
from difflib import SequenceMatcher


class TicketDuplicateDetector:

    def __init__(self, similarity_threshold: float = 0.70):
        self.similarity_threshold = similarity_threshold

    def _normalize(self, text: str) -> str:
        return " ".join(
            str(text).lower().strip().split()
        )

    def _similarity(
        self,
        first_text: str,
        second_text: str
    ) -> float:

        first = self._normalize(first_text)
        second = self._normalize(second_text)

        return SequenceMatcher(
            None,
            first,
            second
        ).ratio()

    def _ticket_text(self, ticket: Dict[str, Any]) -> str:

        fields = [
            ticket.get("customer"),
            ticket.get("order"),
            ticket.get("product"),
            ticket.get("issue")
        ]

        return " ".join(
            str(value)
            for value in fields
            if value
        )

    def find_duplicates(
        self,
        new_ticket: Dict[str, Any],
        existing_tickets: List[Dict[str, Any]]
    ) -> Dict[str, Any]:

        new_text = self._ticket_text(new_ticket)

        matches = []

        for ticket in existing_tickets:

            existing_text = self._ticket_text(ticket)

            similarity = self._similarity(
                new_text,
                existing_text
            )

            if similarity >= self.similarity_threshold:
                matches.append({
                    "ticket_id": ticket.get("ticket_id"),
                    "similarity": round(similarity, 2)
                })

        return {
            "is_duplicate": len(matches) > 0,
            "matches": matches
        }

    def find_related(
        self,
        new_ticket: Dict[str, Any],
        existing_tickets: List[Dict[str, Any]],
        related_threshold: float = 0.60
    ) -> Dict[str, Any]:

        new_issue = self._normalize(
            new_ticket.get("issue", "")
        )

        related_tickets = []

        for ticket in existing_tickets:

            existing_issue = self._normalize(
                ticket.get("issue", "")
            )

            similarity = self._similarity(
                new_issue,
                existing_issue
            )

            same_order = (
                new_ticket.get("order") is not None
                and new_ticket.get("order")
                == ticket.get("order")
            )

            same_product = (
                new_ticket.get("product") is not None
                and new_ticket.get("product")
                == ticket.get("product")
            )

            if (
                similarity >= related_threshold
                or same_order
                or same_product
            ):
                related_tickets.append({
                    "ticket_id": ticket.get("ticket_id"),
                    "similarity": round(similarity, 2),
                    "same_order": same_order,
                    "same_product": same_product
                })

        return {
            "is_related": len(related_tickets) > 0,
            "related_tickets": related_tickets
        }


if __name__ == "__main__":

    detector = TicketDuplicateDetector()

    existing_tickets = [
        {
            "ticket_id": "TICKET-001",
            "customer": "John",
            "order": "ORD-12345",
            "product": "Premium Laptop",
            "issue": "Customer was charged twice"
        },
        {
            "ticket_id": "TICKET-002",
            "customer": "Sarah",
            "order": "ORD-67890",
            "product": "Wireless Mouse",
            "issue": "Mouse is not working"
        }
    ]

    new_ticket = {
        "customer": "John",
        "order": "ORD-12345",
        "product": "Premium Laptop",
        "issue": "There is another duplicate charge"
    }

    result = detector.find_related(
        new_ticket=new_ticket,
        existing_tickets=existing_tickets
    )

    print(result)