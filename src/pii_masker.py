import re


class PIIMasker:
    """
    Masks personally identifiable information and payment data
    before customer evidence is logged or stored.
    """

    def mask_email(self, text):
        return re.sub(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
            "[EMAIL_MASKED]",
            text
        )

    def mask_phone(self, text):
        return re.sub(
            r"(?<!\d)(?:\+?\d[\d\s().-]{8,}\d)(?!\d)",
            "[PHONE_MASKED]",
            text
        )

    def mask_card_number(self, text):
        return re.sub(
            r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)",
            "[CARD_MASKED]",
            text
        )

    def mask_cvv(self, text):
        return re.sub(
            r"\b(?:cvv|cvc|security\s+code)"
            r"\s*[:#-]?\s*\d{3,4}\b",
            "[CVV_MASKED]",
            text,
            flags=re.IGNORECASE
        )

    def mask_account_number(self, text):
        return re.sub(
            r"\b(?:account|a/c|acct)"
            r"\s*(?:number|no|#)?"
            r"\s*[:#-]?\s*\d{6,18}\b",
            "[ACCOUNT_MASKED]",
            text,
            flags=re.IGNORECASE
        )

    def mask_upi(self, text):
        return re.sub(
            r"\b[A-Za-z0-9._-]{2,}@[A-Za-z]{2,}\b",
            "[UPI_MASKED]",
            text
        )

    def mask(self, text):
        if not text:
            return text

        masked = text

        masked = self.mask_email(masked)
        masked = self.mask_cvv(masked)
        masked = self.mask_card_number(masked)
        masked = self.mask_account_number(masked)
        masked = self.mask_upi(masked)
        masked = self.mask_phone(masked)

        return masked

    def mask_dict(self, data):

        if not isinstance(data, dict):
            return data

        masked_data = {}

        for key, value in data.items():

            if isinstance(value, list):

                masked_data[key] = [
                    self.mask(str(item))
                    for item in value
                ]

            elif isinstance(value, str):

                masked_data[key] = self.mask(value)

            else:

                masked_data[key] = value

        return masked_data