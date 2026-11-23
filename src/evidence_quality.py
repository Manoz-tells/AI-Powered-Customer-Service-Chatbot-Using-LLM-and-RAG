class EvidenceQualityChecker:
    """
    Checks whether extracted evidence is usable and whether
    the extracted text contains enough information for verification.
    """

    MIN_TEXT_LENGTH = 10

    def check_text_quality(self, text):
        if not text or not text.strip():
            return {
                "quality": "LOW",
                "usable": False,
                "reason": "NO_TEXT_EXTRACTED"
            }

        cleaned_text = text.strip()

        if len(cleaned_text) < self.MIN_TEXT_LENGTH:
            return {
                "quality": "LOW",
                "usable": False,
                "reason": "TEXT_TOO_SHORT"
            }

        # Very little alphanumeric content usually indicates
        # a blurred, corrupted, or otherwise unreadable file.
        alphanumeric_count = sum(
            character.isalnum()
            for character in cleaned_text
        )

        if alphanumeric_count < 10:
            return {
                "quality": "LOW",
                "usable": False,
                "reason": "INSUFFICIENT_READABLE_CONTENT"
            }

        return {
            "quality": "GOOD",
            "usable": True,
            "reason": "TEXT_READABLE"
        }

    def check_evidence(self, evidence):
        if not evidence:
            return {
                "quality": "LOW",
                "usable": False,
                "reason": "NO_EVIDENCE"
            }

        evidence_count = sum(
            len(values)
            for values in evidence.values()
            if isinstance(values, list)
        )

        if evidence_count == 0:
            return {
                "quality": "LOW",
                "usable": False,
                "reason": "NO_STRUCTURED_EVIDENCE"
            }

        return {
            "quality": "GOOD",
            "usable": True,
            "reason": "STRUCTURED_EVIDENCE_FOUND",
            "evidence_count": evidence_count
        }

    def check(self, text, evidence):
        text_result = self.check_text_quality(text)
        evidence_result = self.check_evidence(evidence)

        if not text_result["usable"]:
            return {
                "quality": "LOW",
                "usable": False,
                "reason": text_result["reason"],
                "text_check": text_result,
                "evidence_check": evidence_result
            }

        if not evidence_result["usable"]:
            return {
                "quality": "LOW",
                "usable": False,
                "reason": evidence_result["reason"],
                "text_check": text_result,
                "evidence_check": evidence_result
            }

        return {
            "quality": "GOOD",
            "usable": True,
            "reason": "EVIDENCE_QUALITY_ACCEPTABLE",
            "text_check": text_result,
            "evidence_check": evidence_result
        }