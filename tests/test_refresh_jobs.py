"""Tests for background refresh job tracking."""

from __future__ import annotations

from threading import Event
import time
import unittest

from src.refresh_jobs import RefreshJobManager


class RefreshJobManagerTests(unittest.TestCase):
    def test_job_completes_and_exposes_result(self) -> None:
        manager = RefreshJobManager()
        job = manager.start("2026-10-02:2026-10-03", lambda: {"inserted": 5})

        completed = self._wait_for_terminal_state(manager, job["job_id"])

        self.assertEqual(completed["status"], "completed")
        self.assertEqual(completed["result"], {"inserted": 5})

    def test_duplicate_active_job_returns_existing_job(self) -> None:
        manager = RefreshJobManager()
        release = Event()
        first = manager.start("same-range", lambda: release.wait(timeout=1))
        second = manager.start("same-range", lambda: "should not run")
        release.set()

        self.assertEqual(second["job_id"], first["job_id"])

    def test_job_failure_is_available_to_pollers(self) -> None:
        manager = RefreshJobManager()

        def fail() -> None:
            raise RuntimeError("NHL feed unavailable")

        job = manager.start("failure", fail)
        failed = self._wait_for_terminal_state(manager, job["job_id"])

        self.assertEqual(failed["status"], "failed")
        self.assertEqual(failed["error"], "NHL feed unavailable")

    def _wait_for_terminal_state(
        self,
        manager: RefreshJobManager,
        job_id: str,
    ) -> dict[str, object]:
        for _ in range(100):
            job = manager.get(job_id)
            assert job is not None
            if job["status"] in {"completed", "failed"}:
                return job
            time.sleep(0.01)
        self.fail("job did not reach a terminal state")
