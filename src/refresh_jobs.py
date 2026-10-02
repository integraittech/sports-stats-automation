"""In-process background job tracking for long-running refresh work."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from typing import Any, Callable
from uuid import uuid4


class RefreshJobManager:
    """Run one refresh at a time and expose small polling snapshots."""

    def __init__(self) -> None:
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._jobs: dict[str, dict[str, Any]] = {}
        self._lock = Lock()

    def start(self, key: str, task: Callable[[], Any]) -> dict[str, Any]:
        with self._lock:
            for job in self._jobs.values():
                if job["key"] == key and job["status"] in {"queued", "running"}:
                    return self._snapshot(job)

            job_id = uuid4().hex
            job = {
                "error": None,
                "id": job_id,
                "key": key,
                "result": None,
                "status": "queued",
            }
            self._jobs[job_id] = job
            self._prune_finished_jobs()
            self._executor.submit(self._run, job_id, task)
            return self._snapshot(job)

    def get(self, job_id: str) -> dict[str, Any] | None:
        with self._lock:
            job = self._jobs.get(job_id)
            return self._snapshot(job) if job else None

    def _run(self, job_id: str, task: Callable[[], Any]) -> None:
        with self._lock:
            self._jobs[job_id]["status"] = "running"

        try:
            result = task()
        except Exception as error:
            with self._lock:
                self._jobs[job_id]["error"] = str(error)
                self._jobs[job_id]["status"] = "failed"
            return

        with self._lock:
            self._jobs[job_id]["result"] = result
            self._jobs[job_id]["status"] = "completed"

    def _prune_finished_jobs(self) -> None:
        finished_ids = [
            job_id
            for job_id, job in self._jobs.items()
            if job["status"] in {"completed", "failed"}
        ]
        for job_id in finished_ids[:-20]:
            del self._jobs[job_id]

    @staticmethod
    def _snapshot(job: dict[str, Any]) -> dict[str, Any]:
        return {
            "error": job["error"],
            "job_id": job["id"],
            "result": job["result"],
            "status": job["status"],
        }
