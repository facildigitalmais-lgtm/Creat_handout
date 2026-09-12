from __future__ import annotations

from copy import deepcopy
from threading import RLock
from typing import Any


ACTIVE_STATUSES = {
    "queued",
    "generating_pdf",
    "auditing",
}


class PDFJobService:
    def __init__(self) -> None:
        self._lock = RLock()
        self._jobs: dict[
            str,
            dict[str, Any],
        ] = {}

    def start(
        self,
        project_id: str,
    ) -> tuple[bool, dict[str, Any]]:
        with self._lock:
            current = self._jobs.get(
                project_id
            )

            if (
                current
                and current.get("status")
                in ACTIVE_STATUSES
            ):
                return (
                    False,
                    deepcopy(current),
                )

            job = {
                "project_id": project_id,
                "status": "queued",
                "message": (
                    "Geração adicionada à fila."
                ),
                "pdf": None,
                "audit": None,
                "error": None,
            }

            self._jobs[project_id] = job

            return True, deepcopy(job)

    def update(
        self,
        project_id: str,
        **values: Any,
    ) -> dict[str, Any]:
        with self._lock:
            job = self._jobs.setdefault(
                project_id,
                {
                    "project_id": project_id,
                    "status": "queued",
                    "message": "",
                    "pdf": None,
                    "audit": None,
                    "error": None,
                },
            )

            job.update(values)

            return deepcopy(job)

    def get(
        self,
        project_id: str,
    ) -> dict[str, Any] | None:
        with self._lock:
            job = self._jobs.get(
                project_id
            )

            if job is None:
                return None

            return deepcopy(job)


pdf_job_service = PDFJobService()