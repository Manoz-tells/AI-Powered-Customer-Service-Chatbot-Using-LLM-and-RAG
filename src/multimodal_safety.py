import re


class MultimodalSafetyGuard:
    """
    Detects prompt-injection instructions hidden inside
    uploaded files or extracted OCR/PDF text.
    """

    def __init__(self):
        self.patterns = [
            r"ignore\s+(all\s+)?previous\s+instructions",
            r"ignore\s+(all\s+)?prior\s+instructions",
            r"disregard\s+(all\s+)?previous\s+instructions",
            r"disregard\s+(all\s+)?prior\s+instructions",
            r"ignore\s+system\s+instructions",
            r"reveal\s+(the\s+)?system\s+prompt",
            r"show\s+(the\s+)?system\s+prompt",
            r"print\s+(the\s+)?system\s+prompt",
            r"override\s+(the\s+)?system\s+instructions",
            r"bypass\s+(the\s+)?system\s+instructions",
            r"follow\s+these\s+instructions",
            r"you\s+are\s+now\s+an?\s+assistant",
            r"forget\s+(everything|all)\s+above"
        ]

    def scan(self, text):
        if not text:
            return {
                "safe": True,
                "detected_patterns": []
            }

        detected_patterns = []

        for pattern in self.patterns:
            if re.search(pattern, text, re.IGNORECASE):
                detected_patterns.append(pattern)

        return {
            "safe": len(detected_patterns) == 0,
            "detected_patterns": detected_patterns
        }

    def validate(self, text):
        result = self.scan(text)

        if result["safe"]:
            return {
                "safe": True,
                "action": "ALLOW",
                "reason": "NO_PROMPT_INJECTION_DETECTED"
            }

        return {
            "safe": False,
            "action": "REJECT",
            "reason": "PROMPT_INJECTION_DETECTED",
            "detected_patterns": result["detected_patterns"]
        }