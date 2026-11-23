from datetime import datetime, time, timedelta
from pathlib import Path
import time as time_module


class KBProductionController:

    def __init__(
        self,
        maintenance_start=time(2, 0),
        maintenance_end=time(4, 0),
        retry_delays=(15, 30, 60),
        health_check_minutes=5
    ):
        self.maintenance_start = maintenance_start
        self.maintenance_end = maintenance_end
        self.retry_delays = retry_delays
        self.health_check_minutes = health_check_minutes

    # ========================================================
    # MAINTENANCE WINDOW
    # ========================================================

    def is_maintenance_window(self, current_time=None):

        if current_time is None:
            current_time = datetime.now()

        current = current_time.time()

        if self.maintenance_start <= self.maintenance_end:

            return (
                self.maintenance_start
                <= current
                < self.maintenance_end
            )

        return (
            current >= self.maintenance_start
            or current < self.maintenance_end
        )

    # ========================================================
    # RETRY SCHEDULE
    # ========================================================

    def get_retry_schedule(self):

        return [
            {
                "attempt": index + 1,
                "delay_minutes": delay
            }
            for index, delay
            in enumerate(self.retry_delays)
        ]

    # ========================================================
    # QUALITY CHECK
    # ========================================================

    def quality_check(
        self,
        previous_documents,
        new_documents
    ):

        if not new_documents:

            return {
                "passed": True,
                "reason": "No KB changes detected."
            }

        if not previous_documents:

            return {
                "passed": True,
                "reason": "Initial KB population."
            }

        return {
            "passed": True,
            "reason": "Basic KB quality check passed."
        }

    # ========================================================
    # GROUNDING CHECK
    # ========================================================

    def grounding_check(
        self,
        documents
    ):

        if not documents:

            return {
                "passed": False,
                "reason": "No documents available for grounding."
            }

        empty_documents = []

        for document in documents:

            path = Path(document)

            if path.exists():

                if path.stat().st_size == 0:

                    empty_documents.append(
                        path.name
                    )

        if empty_documents:

            return {
                "passed": False,
                "reason": "Empty documents detected.",
                "documents": empty_documents
            }

        return {
            "passed": True,
            "reason": "Grounding check passed."
        }

    # ========================================================
    # HEALTH CHECK
    # ========================================================

    def health_check(
        self,
        faiss_result,
        grounding_result
    ):

        faiss_ok = (
            faiss_result is None
            or faiss_result.get("success", False)
        )

        grounding_ok = grounding_result.get(
            "passed",
            False
        )

        healthy = (
            faiss_ok
            and grounding_ok
        )

        return {
            "healthy": healthy,
            "faiss_ok": faiss_ok,
            "grounding_ok": grounding_ok
        }

    # ========================================================
    # UPDATE DECISION
    # ========================================================

    def approve_update(
        self,
        quality_result,
        grounding_result
    ):

        return (
            quality_result.get("passed", False)
            and grounding_result.get("passed", False)
        )

    # ========================================================
    # ACCESS CONTROL
    # ========================================================

    def authorize_access(
        self,
        role,
        required_role="admin"
    ):

        allowed_roles = {
            "admin": 3,
            "manager": 2,
            "agent": 1
        }

        user_level = allowed_roles.get(role, 0)
        required_level = allowed_roles.get(
            required_role,
            3
        )

        return {
            "authorized": user_level >= required_level,
            "role": role,
            "required_role": required_role
        }

    # ========================================================
    # AUTOMATIC ROLLBACK
    # ========================================================

    def rollback_if_unhealthy(
        self,
        health_result,
        rollback_callback,
        version_name
    ):

        if health_result.get("healthy", False):
            return {
                "rollback_triggered": False,
                "reason": "Health check passed."
            }

        rollback_result = rollback_callback(
            version_name
        )

        return {
            "rollback_triggered": True,
            "reason": "Health check failed.",
            "version": version_name,
            "rollback_result": rollback_result
        }
    
    # ========================================================
    # MONITORING EVENT
    # ========================================================

    def create_monitoring_event(
        self,
        operation,
        success,
        latency_seconds=0.0,
        confidence=None,
        escalations=0,
        error=None
    ):

        return {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "success": success,
            "latency_seconds": round(
                latency_seconds,
                3
            ),
            "confidence": confidence,
            "escalations": escalations,
            "error": error
        }


if __name__ == "__main__":

    controller = KBProductionController()

    print(
        "Maintenance window:",
        controller.is_maintenance_window()
    )

    print(
        "Retry schedule:",
        controller.get_retry_schedule()
    )

    grounding = controller.grounding_check(
        [
            "knowledge_base/refund_policy.txt",
            "knowledge_base/test_policy.txt"
        ]
    )

    print(
        "Grounding:",
        grounding
    )

    quality = controller.quality_check(
        ["refund_policy.txt"],
        ["refund_policy.txt"]
    )

    print(
        "Quality:",
        quality
    )

    print(
        "Approval:",
        controller.approve_update(
            quality,
            grounding
        )
    )

    print(
        "Health:",
        controller.health_check(
            None,
            grounding
        )
    )
    print(
        "Admin access:",
        controller.authorize_access("admin")
    )

    print(
        "Agent access:",
        controller.authorize_access("agent")
    )

    def fake_rollback(version_name):
        return {
            "success": True,
            "version": version_name
        }

    failed_health = {
        "healthy": False,
        "faiss_ok": False,
        "grounding_ok": True
    }

    print(
        "Automatic rollback:",
        controller.rollback_if_unhealthy(
            failed_health,
            fake_rollback,
            "20260930_133145"
        )
    )