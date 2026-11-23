from datetime import datetime, timedelta
from typing import Dict, Any, List


class SLAManager:

    def __init__(
        self,
        sla_minutes: int = 60,
        warning_percentage: float = 0.75,
        business_start_hour: int = 9,
        business_end_hour: int = 18,
        weekends: List[int] = None,
        holidays: List[str] = None
    ):
        self.sla_minutes = sla_minutes
        self.warning_percentage = warning_percentage
        self.business_start_hour = business_start_hour
        self.business_end_hour = business_end_hour

        # Monday = 0, Sunday = 6
        self.weekends = (
            weekends
            if weekends is not None
            else [5, 6]
        )

        self.holidays = set(
            holidays
            if holidays is not None
            else []
        )

    def _is_working_day(self, current_time: datetime) -> bool:

        if current_time.weekday() in self.weekends:
            return False

        if current_time.strftime("%Y-%m-%d") in self.holidays:
            return False

        return True

    def _is_within_business_hours(
        self,
        current_time: datetime
    ) -> bool:

        return (
            self.business_start_hour
            <= current_time.hour
            < self.business_end_hour
        )

    def _calculate_working_minutes(
        self,
        start_time: datetime,
        current_time: datetime
    ) -> int:

        if current_time <= start_time:
            return 0

        total_minutes = 0
        cursor = start_time.replace(second=0, microsecond=0)

        while cursor < current_time:

            if (
                self._is_working_day(cursor)
                and self._is_within_business_hours(cursor)
            ):
                total_minutes += 1

            cursor += timedelta(minutes=1)

        return total_minutes

    def check_sla(
        self,
        start_time: datetime,
        current_time: datetime
    ) -> Dict[str, Any]:

        elapsed_minutes = self._calculate_working_minutes(
            start_time,
            current_time
        )

        warning_threshold = (
            self.sla_minutes * self.warning_percentage
        )

        warning = (
            elapsed_minutes >= warning_threshold
            and elapsed_minutes < self.sla_minutes
        )

        breached = elapsed_minutes >= self.sla_minutes

        if breached:
            status = "breached"
        elif warning:
            status = "warning"
        else:
            status = "within_sla"

        return {
            "sla_minutes": self.sla_minutes,
            "elapsed_working_minutes": elapsed_minutes,
            "warning_threshold_minutes": warning_threshold,
            "warning": warning,
            "breached": breached,
            "status": status
        }


if __name__ == "__main__":

    manager = SLAManager(
        sla_minutes=60,
        business_start_hour=9,
        business_end_hour=18
    )

    start = datetime(2026, 9, 11, 10, 0)
    current = datetime(2026, 9, 14, 10, 0)

    result = manager.check_sla(
        start_time=start,
        current_time=current
    )

    print(result)