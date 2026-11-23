from typing import Dict, Any


class TicketPriorityCalculator:

    def calculate(
        self,
        severity: str,
        sentiment: str,
        waiting_minutes: int,
        customer_impact: str,
        sla_breached: bool = False
    ) -> Dict[str, Any]:

        score = 0
        reasons = []

        severity_scores = {
            "low": 1,
            "medium": 2,
            "high": 3,
            "critical": 4
        }

        sentiment_scores = {
            "positive": 0,
            "neutral": 0,
            "negative": 1,
            "frustrated": 2,
            "urgent": 3,
            "sarcastic": 1
        }

        impact_scores = {
            "low": 1,
            "medium": 2,
            "high": 3,
            "critical": 4
        }

        severity = severity.lower()
        sentiment = sentiment.lower()
        customer_impact = customer_impact.lower()

        severity_score = severity_scores.get(severity, 2)
        sentiment_score = sentiment_scores.get(sentiment, 0)
        impact_score = impact_scores.get(customer_impact, 2)

        score += severity_score
        score += sentiment_score
        score += impact_score

        if severity_score >= 3:
            reasons.append("high severity")

        if sentiment_score >= 2:
            reasons.append("negative or urgent sentiment")

        if impact_score >= 3:
            reasons.append("high customer impact")

        if waiting_minutes >= 15:
            score += 2
            reasons.append("extended waiting time")
        elif waiting_minutes >= 5:
            score += 1
            reasons.append("customer waiting")

        if sla_breached:
            score += 4
            reasons.append("SLA breached")

        if score >= 12:
            priority = "critical"
        elif score >= 9:
            priority = "high"
        elif score >= 5:
            priority = "medium"
        else:
            priority = "low"

        return {
            "priority": priority,
            "score": score,
            "reasons": reasons
        }


if __name__ == "__main__":

    calculator = TicketPriorityCalculator()

    result = calculator.calculate(
        severity="high",
        sentiment="frustrated",
        waiting_minutes=20,
        customer_impact="high",
        sla_breached=False
    )

    print(result)