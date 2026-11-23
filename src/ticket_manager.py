from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
import json


@dataclass
class SupportTicket:
    customer: Optional[str] = None
    order: Optional[str] = None
    product: Optional[str] = None
    issue: Optional[str] = None
    evidence: Optional[str] = None
    contact_details: Optional[str] = None


class TicketManager:

    def create_ticket(
        self,
        customer: Optional[str] = None,
        order: Optional[str] = None,
        product: Optional[str] = None,
        issue: Optional[str] = None,
        evidence: Optional[str] = None,
        contact_details: Optional[str] = None
    ) -> Dict[str, Any]:

        ticket = SupportTicket(
            customer=customer,
            order=order,
            product=product,
            issue=issue,
            evidence=evidence,
            contact_details=contact_details
        )

        return asdict(ticket)


if __name__ == "__main__":

    manager = TicketManager()

    ticket = manager.create_ticket(
        customer="John",
        order="ORD-12345",
        product="Premium Laptop",
        issue="Customer was charged twice.",
        evidence="Invoice showing two identical charges.",
        contact_details="john@example.com"
    )

    print(json.dumps(ticket, indent=2))