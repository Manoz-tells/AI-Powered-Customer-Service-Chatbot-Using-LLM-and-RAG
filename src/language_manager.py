import re


class LanguageManager:

    SUPPORTED_LANGUAGES = {
        "en": "English",
        "hi": "Hindi",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "mixed": "Mixed Language"
    }

    def __init__(self):
        self.language_keywords = {
            "hi": [
                "hai", "hain", "mujhe", "mera", "meri",
                "aap", "kya", "nahi", "chahiye", "kripya"
            ],
            "es": [
                "hola", "gracias", "quiero", "necesito",
                "pedido", "problema", "ayuda", "por", "favor"
            ],
            "fr": [
                "bonjour", "merci", "je", "besoin",
                "commande", "probleme", "aide"
            ],
            "de": [
                "hallo", "danke", "ich", "brauche",
                "bestellung", "problem", "hilfe"
            ]
        }

    def detect_language(self, message):
        text = message.lower()

        scores = {
            language: sum(
                1 for word in keywords
                if re.search(r"\b" + re.escape(word) + r"\b", text)
            )
            for language, keywords in self.language_keywords.items()
        }

        detected = max(
            scores,
            key=scores.get
        )

        if scores[detected] == 0:
            return "en", 0.90

        total = sum(scores.values())

        confidence = min(
            0.99,
            0.70 + (scores[detected] / total) * 0.29
        )

        return detected, confidence

    def detect_mixed_language(self, message):
        text = message.lower()

        detected_languages = []

        for language, keywords in self.language_keywords.items():

            if any(
                re.search(
                    r"\b" + re.escape(word) + r"\b",
                    text
                )
                for word in keywords
            ):
                detected_languages.append(language)

        return len(detected_languages) > 1

    def extract_identifiers(self, message):

        patterns = [
            r"\bORD[-_][A-Z0-9-]+\b",
            r"\bTICKET[-_][A-Z0-9-]+\b",
            r"\b[A-Z]{2,5}-\d{3,}\b",
            r"\b\d{10,}\b"
        ]

        identifiers = []

        for pattern in patterns:
            identifiers.extend(
                re.findall(
                    pattern,
                    message,
                    re.IGNORECASE
                )
            )

        return list(dict.fromkeys(identifiers))

    def process_message(self, message):

        language, confidence = self.detect_language(
            message
        )

        mixed_language = (
            self.detect_mixed_language(message)
        )

        if mixed_language:
            language_name = "Mixed Language"
        else:
            language_name = self.SUPPORTED_LANGUAGES.get(
                language,
                "English"
            )

        identifiers = self.extract_identifiers(
            message
        )

        return {
            "language": language,
            "language_name": language_name,
            "confidence": confidence,
            "mixed_language": mixed_language,
            "identifiers": identifiers
        }