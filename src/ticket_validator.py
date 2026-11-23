from typing import Dict, Any, List


class TicketValidator:

    REQUIRED_FIELDS = [
        "customer",
        "issue",
        "contact_details"
    ]

    def validate(self, ticket: Dict[str, Any]) -> Dict[str, Any]:

        missing_fields: List[str] = []

        for field in self.REQUIRED_FIELDS:
            value = ticket.get(field)

            if value is None or str(value).strip() == "":
                missing_fields.append(field)

        if missing_fields:
            clarification = self._create_clarification_message(
                missing_fields
            )

            return {
                "complete": False,
                "missing_fields": missing_fields,
                "clarification_message": clarification
            }

        return {
            "complete": True,
            "missing_fields": [],
            "clarification_message": None
        }

    def _create_clarification_message(
        self,
        missing_fields: List[str]
    ) -> str:

        field_messages = {
            "customer": "your name",
            "issue": "a description of the issue",
            "contact_details": "your contact details"
        }

        requested_items = [
            field_messages[field]
            for field in missing_fields
        ]

        if len(requested_items) == 1:
            request_text = requested_items[0]
        elif len(requested_items) == 2:
            request_text = (
                requested_items[0]
                + " and "
                + requested_items[1]
            )
        else:
            request_text = (
                ", ".join(requested_items[:-1])
                + ", and "
                + requested_items[-1]
            )

        return (
            "To create your support ticket, please provide "
            + request_text
            + "."
        )


if __name__ == "__main__":

    validator = TicketValidator()

    incomplete_ticket = {
        "customer": None,
        "order": "ORD-12345",
        "product": "Premium Laptop",
        "issue": "Charged twice",
        "evidence": None,
        "contact_details": None
    }

    result = validator.validate(incomplete_ticket)

    print(result)
    