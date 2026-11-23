import re


class EvidenceComparator:
    """
    Compares extracted evidence from customer files with
    information provided in the customer's message.
    """

    def normalize(self, value):
        if value is None:
            return ""

        return re.sub(
            r"[^a-zA-Z0-9]",
            "",
            str(value)
        ).lower()

    def compare_field(self, field_name, evidence_values, message):
        message_normalized = self.normalize(message)

        if not evidence_values:
            return {
                "field": field_name,
                "status": "MISSING_EVIDENCE",
                "evidence": []
            }

        matches = []
        conflicts = []
        not_provided = []

        for value in evidence_values:
            normalized_value = self.normalize(value)

            if normalized_value in message_normalized:
                matches.append(value)
            else:
                not_provided.append(value)

        # If the customer explicitly mentions a different value
        # for the same field, mark it as a conflict.
        if field_name == "amounts":
            customer_amounts = re.findall(
                r"(?:₹|\$|€|£|Rs\.?|INR)"
                r"\s*[\d,]+(?:\.\d{1,2})?",
                message,
                re.IGNORECASE
            )

            if customer_amounts:
                evidence_normalized = {
                    self.normalize(value)
                    for value in evidence_values
                }

                for amount in customer_amounts:
                    if self.normalize(amount) not in evidence_normalized:
                        conflicts.append(amount)

        if field_name == "order_ids":
            customer_orders = re.findall(
                r"\b(?:order[\s_-]*id|order)"
                r"[\s:#-]*([A-Z0-9-]{4,})\b",
                message,
                re.IGNORECASE
            )

            for order in customer_orders:
                if self.normalize(order) not in {
                    self.normalize(value)
                    for value in evidence_values
                }:
                    conflicts.append(order)

        if matches and not conflicts:
            status = "MATCH"
        elif conflicts:
            status = "CONFLICT"
        else:
            status = "NOT_PROVIDED"

        return {
            "field": field_name,
            "status": status,
            "evidence": evidence_values,
            "matches": matches,
            "conflicts": conflicts,
            "not_provided": not_provided
        }

    def compare(self, customer_message, evidence):
        if not customer_message:
            return {
                "status": "CLARIFICATION_REQUIRED",
                "reason": "CUSTOMER_MESSAGE_MISSING",
                "fields": []
            }

        if not evidence:
            return {
                "status": "CLARIFICATION_REQUIRED",
                "reason": "EVIDENCE_MISSING",
                "fields": []
            }

        fields = []

        fields.append(
            self.compare_field(
                "order_ids",
                evidence.get("order_ids", []),
                customer_message
            )
        )

        fields.append(
            self.compare_field(
                "dates",
                evidence.get("dates", []),
                customer_message
            )
        )

        fields.append(
            self.compare_field(
                "amounts",
                evidence.get("amounts", []),
                customer_message
            )
        )

        fields.append(
            self.compare_field(
                "product_names",
                evidence.get("product_names", []),
                customer_message
            )
        )

        fields.append(
            self.compare_field(
                "error_codes",
                evidence.get("error_codes", []),
                customer_message
            )
        )

        conflicts = [
            field
            for field in fields
            if field["status"] == "CONFLICT"
        ]

        matches = [
            field
            for field in fields
            if field["status"] == "MATCH"
        ]

        if conflicts:
            overall_status = "CONFLICT_DETECTED"
            reason = "Evidence conflicts with customer message."
        elif matches:
            overall_status = "EVIDENCE_MATCHED"
            reason = "Evidence matches available customer information."
        else:
            overall_status = "CLARIFICATION_REQUIRED"
            reason = "Insufficient information to verify evidence."

        return {
            "status": overall_status,
            "reason": reason,
            "fields": fields
        }