from typing import Dict, Any, List


class TicketRouter:

    def __init__(
        self,
        business_start_hour: int = 9,
        business_end_hour: int = 18
    ):
        self.business_start_hour = business_start_hour
        self.business_end_hour = business_end_hour

    def route_ticket(
        self,
        issue_type: str,
        agents: List[Dict[str, Any]],
        current_hour: int
    ) -> Dict[str, Any]:

        within_business_hours = (
            self.business_start_hour
            <= current_hour
            < self.business_end_hour
        )

        if not within_business_hours:
            return {
                "assigned": False,
                "agent": None,
                "reason": "Outside business hours",
                "queue": "after_hours"
            }

        suitable_agents = []

        for agent in agents:

            if not agent.get("available", False):
                continue

            skills = [
                skill.lower()
                for skill in agent.get("skills", [])
            ]

            if issue_type.lower() not in skills:
                continue

            suitable_agents.append(agent)

        if not suitable_agents:
            return {
                "assigned": False,
                "agent": None,
                "reason": "No available agent with required skill",
                "queue": "unassigned"
            }

        selected_agent = min(
            suitable_agents,
            key=lambda agent: agent.get("workload", 0)
        )

        return {
            "assigned": True,
            "agent": selected_agent["name"],
            "reason": "Agent selected by skill, availability, and workload",
            "queue": "assigned"
        }


if __name__ == "__main__":

    router = TicketRouter()

    agents = [
        {
            "name": "Agent A",
            "skills": ["refund"],
            "available": True,
            "workload": 5
        },
        {
            "name": "Agent B",
            "skills": ["technical"],
            "available": True,
            "workload": 2
        },
        {
            "name": "Agent C",
            "skills": ["payment"],
            "available": False,
            "workload": 0
        }
    ]

    result = router.route_ticket(
        issue_type="payment",
        agents=agents,
        current_hour=14
    )

    print(result)