from datetime import datetime, time
from typing import Dict, Any


class EscalationEngine:

    def __init__(
        self,
        business_start: time = time(9, 0),
        business_end: time = time(18, 0),
        unresolved_limit_minutes: int = 15
    ):
        self.business_start = business_start
        self.business_end = business_end
        self.unresolved_limit_minutes = unresolved_limit_minutes

    def evaluate(
        self,
        message: str,
        sentiment: str,
        confidence: float,
        conversation_start: datetime,
        current_time: datetime = None,
        conversation_history: list = None
    ) -> Dict[str, Any]:

        if current_time is None:
            current_time = datetime.now()

        if conversation_history is None:
            conversation_history = []

        recent_history = conversation_history[-10:]

        full_conversation = " ".join(
            recent_history + [message]
        ).lower()

        current_text = message.lower()

        reasons = []
        conditions = []

        # ====================================================
        # ACCOUNT COMPROMISE
        # ====================================================

        account_compromise_terms = [
            "account hacked",
            "account compromised",
            "someone accessed my account",
            "someone has accessed my account",
            "someone got into my account",
            "someone logged into my account",
            "someone has logged into my account",
            "unauthorized access",
            "unauthorized login",
            "unauthorized activity on my account"
        ]

        if any(
            term in full_conversation
            for term in account_compromise_terms
        ):
            reasons.append("Possible account compromise")
            conditions.append("account_compromise")

        # ====================================================
        # DUPLICATE PAYMENT
        # ====================================================

        duplicate_payment_terms = [
            "charged twice",
            "charged two times",
            "duplicate payment",
            "duplicate charge",
            "charged twice for"
        ]

        if any(
            term in full_conversation
            for term in duplicate_payment_terms
        ):
            reasons.append("Possible duplicate payment")
            conditions.append("duplicate_payment")

        # ====================================================
        # LEGAL THREAT
        # Only inspect the current message to avoid false
        # positives from unrelated historical messages.
        # ====================================================

        legal_terms = [
            "sue",
            "lawsuit",
            "legal action",
            "lawyer",
            "attorney",
            "consumer court"
        ]

        if any(
            term in current_text
            for term in legal_terms
        ):
            reasons.append(
                "Legal threat or legal escalation"
            )
            conditions.append("legal_threat")

        # ====================================================
        # BUSINESS HOURS
        # ====================================================

        current_clock = current_time.time()

        business_hours = (
            self.business_start
            <= current_clock
            < self.business_end
        )

        # ====================================================
        # AFTER-HOURS URGENT
        # ====================================================

        after_hours_urgent = (
            sentiment == "urgent"
            and not business_hours
        )

        if after_hours_urgent:
            reasons.append(
                "Urgent complaint received after business hours"
            )
            conditions.append("after_hours_urgent")

        # ====================================================
        # WAITING TIME
        # ====================================================

        waiting_minutes = (
            current_time - conversation_start
        ).total_seconds() / 60

        # ====================================================
        # NEGATIVE TIMEOUT
        # ====================================================

        unresolved_negative = (
            sentiment in {
                "negative",
                "frustrated",
                "urgent"
            }
            and waiting_minutes > self.unresolved_limit_minutes
        )

        if unresolved_negative:
            reasons.append(
                "Negative conversation unresolved for more than "
                f"{self.unresolved_limit_minutes} minutes"
            )
            conditions.append("negative_timeout")

        # ====================================================
        # ESCALATION DECISION
        # ====================================================

        should_escalate = len(conditions) > 0

        if after_hours_urgent:
            queue = "on-call"
        elif should_escalate:
            queue = "priority-escalation"
        else:
            queue = "normal"

        # ====================================================
        # RESULT
        # ====================================================

        return {
            "escalate": should_escalate,
            "queue": queue,
            "conditions": conditions,
            "reasons": reasons,
            "waiting_minutes": round(
                waiting_minutes,
                2
            ),
            "escalated_at": (
                current_time.isoformat()
                if should_escalate
                else None
            )
        }

    def create_escalation_record(
        self,
        escalation_result: Dict[str, Any],
        conversation_history: list,
        current_message: str
    ) -> Dict[str, Any]:

        if not escalation_result["escalate"]:
            return {
                "escalated": False,
                "record": None
            }

        conversation = (
            conversation_history[-10:]
            + [current_message]
        )

        summary = " ".join(
            conversation
        )

        record = {
            "reason": escalation_result["reasons"],
            "activated_conditions": (
                escalation_result["conditions"]
            ),
            "conversation_summary": summary,
            "queue": escalation_result["queue"],
            "waiting_minutes": (
                escalation_result["waiting_minutes"]
            ),
            "escalated_at": (
                escalation_result["escalated_at"]
            )
        }

        return {
            "escalated": True,
            "record": record
        }


if __name__ == "__main__":

    engine = EscalationEngine()

    start_time = datetime(
        2026,
        9,
        10,
        10,
        0
    )

    current_time = datetime(
        2026,
        9,
        10,
        10,
        5
    )

    history = [
        "My payment was charged twice.",
        "I already contacted support about this.",
        "Nobody has fixed the duplicate payment."
    ]

    current_message = (
        "Can you please resolve this?"
    )

    result = engine.evaluate(
        message=current_message,
        sentiment="frustrated",
        confidence=0.95,
        conversation_start=start_time,
        current_time=current_time,
        conversation_history=history
    )

    record = engine.create_escalation_record(
        escalation_result=result,
        conversation_history=history,
        current_message=current_message
    )

    print(record)