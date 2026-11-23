from datetime import datetime
from typing import Dict, Any, List

from ticket_extractor import TicketExtractor
from ticket_validator import TicketValidator
from ticket_priority import TicketPriorityCalculator
from ticket_duplicate_detector import TicketDuplicateDetector
from sla_manager import SLAManager
from ticket_router import TicketRouter
from ticket_handoff import TicketHandoff


class TicketWorkflow:

    def __init__(self):

        self.extractor = TicketExtractor()
        self.validator = TicketValidator()
        self.priority_calculator = TicketPriorityCalculator()
        self.duplicate_detector = TicketDuplicateDetector()
        self.sla_manager = SLAManager()
        self.router = TicketRouter()
        self.handoff = TicketHandoff()

    def process(
        self,
        message: str,
        existing_tickets: List[Dict[str, Any]],
        start_time: datetime,
        current_time: datetime,
        conversation_history: List[str] = None,
        severity: str = "medium",
        sentiment: str = "neutral",
        customer_impact: str = "medium",
        issue_type: str = "general",
        agents: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:

        # 1. Extract ticket information
        ticket = self.extractor.extract(
            message=message,
            conversation_history=conversation_history
        )

        # 2. Validate mandatory information
        validation = self.validator.validate(ticket)

        if not validation["complete"]:
            return {
                "status": "needs_information",
                "ticket": ticket,
                "validation": validation
            }

        # 3. Calculate priority
        sla_result = self.sla_manager.check_sla(
            start_time=start_time,
            current_time=current_time
        )

        priority_result = self.priority_calculator.calculate(
            severity=severity,
            sentiment=sentiment,
            waiting_minutes=sla_result[
                "elapsed_working_minutes"
            ],
            customer_impact=customer_impact,
            sla_breached=sla_result["breached"]
        )

        ticket["priority"] = priority_result["priority"]

        # 4. Check for duplicate tickets
        duplicate_result = self.duplicate_detector.find_duplicates(
            new_ticket=ticket,
            existing_tickets=existing_tickets
        )

        # 5. Check for related tickets
        related_result = self.duplicate_detector.find_related(
            new_ticket=ticket,
            existing_tickets=existing_tickets
        )

        # 6. Route ticket
        if agents is None:
            agents = []

        routing_result = self.router.route_ticket(
            issue_type=issue_type,
            agents=agents,
            current_hour=current_time.hour
        )

        # 7. Create masked handoff summary
        ticket["status"] = "open"

        if duplicate_result["is_duplicate"]:
            ticket["status"] = "duplicate"

        if sla_result["breached"]:
            ticket["status"] = "sla_breached"

        if not routing_result["assigned"]:
            ticket["status"] = "awaiting_assignment"

        handoff_summary = self.handoff.create_summary(
            ticket
        )

        return {
            "status": "ticket_created",
            "ticket": ticket,
            "validation": validation,
            "priority": priority_result,
            "sla": sla_result,
            "duplicate": duplicate_result,
            "related": related_result,
            "routing": routing_result,
            "handoff": handoff_summary
        }


if __name__ == "__main__":

    workflow = TicketWorkflow()

    existing_tickets = [
        {
            "ticket_id": "TICKET-001",
            "customer": "Sarah",
            "order": "ORD-67890",
            "product": "Wireless Mouse",
            "issue": "Mouse is not working"
        }
    ]

    agents = [
        {
            "name": "Agent A",
            "skills": ["payment", "refund"],
            "available": True,
            "workload": 5
        },
        {
            "name": "Agent B",
            "skills": ["payment", "technical"],
            "available": True,
            "workload": 2
        }
    ]

    message = """
    Hi, my name is John.
    My order ORD-12345 for the Premium Laptop was charged twice.
    I have an invoice showing both identical charges.
    You can contact me at john@example.com.
    """

    start_time = datetime(2026, 9, 15, 10, 0)
    current_time = datetime(2026, 9, 15, 10, 20)

    result = workflow.process(
        message=message,
        existing_tickets=existing_tickets,
        start_time=start_time,
        current_time=current_time,
        severity="high",
        sentiment="frustrated",
        customer_impact="high",
        issue_type="payment",
        agents=agents
    )

    print(result)