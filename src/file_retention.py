import time
from pathlib import Path


class FileRetentionManager:
    """
    Manages retention and secure deletion of uploaded customer files.
    """

    def __init__(self, retention_seconds=86400):
        self.retention_seconds = retention_seconds

    def get_file_age(self, file_path):
        path = Path(file_path)

        if not path.exists():
            return None

        return time.time() - path.stat().st_mtime

    def is_expired(self, file_path):
        age = self.get_file_age(file_path)

        if age is None:
            return False

        return age >= self.retention_seconds

    def delete_file(self, file_path):
        path = Path(file_path)

        if not path.exists():
            return {
                "deleted": False,
                "reason": "FILE_NOT_FOUND"
            }

        if not path.is_file():
            return {
                "deleted": False,
                "reason": "NOT_A_FILE"
            }

        try:
            path.unlink()

            return {
                "deleted": True,
                "file_name": path.name,
                "reason": "FILE_DELETED"
            }

        except Exception as error:
            return {
                "deleted": False,
                "reason": "DELETE_FAILED",
                "error": str(error)
            }

    def cleanup_file(self, file_path):
        path = Path(file_path)

        if not path.exists():
            return {
                "deleted": False,
                "reason": "FILE_NOT_FOUND"
            }

        if self.is_expired(file_path):
            return self.delete_file(file_path)

        return {
            "deleted": False,
            "reason": "RETENTION_PERIOD_NOT_EXPIRED"
        }