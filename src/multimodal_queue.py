import json
import os
import threading
import time
import uuid


class MultimodalQueue:
    """
    Handles multimodal processing that may take longer than
    the 30-second response threshold.
    """

    MAX_SYNC_SECONDS = 30

    def __init__(self):
        self.jobs = {}
        self.job_store_file = "multimodal_jobs.json"

    def _run_job(
        self,
        job_id,
        processor,
        file_path,
        on_complete=None
    ):
        self.jobs[job_id]["status"] = "processing"
        self.jobs[job_id]["started_at"] = time.time()

        try:
            result = processor.process(file_path)

            self.jobs[job_id]["status"] = "completed"
            self.jobs[job_id]["result"] = result

            if on_complete:
                on_complete(
                    self.jobs[job_id]
                )

        except Exception as error:
            self.jobs[job_id]["status"] = "failed"
            self.jobs[job_id]["error"] = str(error)

        self.jobs[job_id]["completed_at"] = time.time()

        try:
            if os.path.exists(self.job_store_file):

                with open(
                    self.job_store_file,
                    "r",
                    encoding="utf-8"
                ) as file:

                    saved_jobs = json.load(file)

            else:

                saved_jobs = {}

            saved_jobs[job_id] = {
                **saved_jobs.get(job_id, {}),
                **self.jobs[job_id]
            }

            with open(
                self.job_store_file,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    saved_jobs,
                    file,
                    indent=4
                )

        except Exception:
            pass

    def submit(
        self,
        processor,
        file_path,
        on_complete=None
    ):
        job_id = str(uuid.uuid4())

        self.jobs[job_id] = {
            "job_id": job_id,
            "file_path": file_path,
            "status": "queued",
            "result": None
        }

        worker = threading.Thread(
            target=self._run_job,
            args=(
                job_id,
                processor,
                file_path,
                on_complete
            ),
            daemon=True
        )

        worker.start()

        return {
            "queued": True,
            "job_id": job_id,
            "status": "queued",
            "message": (
                "File processing started in the background."
            )
        }

    def get_status(self, job_id):
        job = self.jobs.get(job_id)

        if not job:
            return {
                "found": False,
                "job_id": job_id,
                "status": "NOT_FOUND"
            }

        return {
            "found": True,
            "job_id": job_id,
            "status": job.get("status"),
            "result": job.get("result"),
            "error": job.get("error")
        }

    def restore_job(self, job):
        job_id = job.get("job_id")

        if not job_id:
            return

        self.jobs[job_id] = {
            "job_id": job_id,
            "file_path": job.get("file_path"),
            "status": job.get("status", "completed"),
            "result": job.get("result"),
            "error": job.get("error")
        }