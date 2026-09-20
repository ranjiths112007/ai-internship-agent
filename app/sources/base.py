from __future__ import annotations

from abc import ABC, abstractmethod
from app.models.schemas import Job


class JobSource(ABC):
    name: str

    @abstractmethod
    def fetch_jobs(self) -> list[Job]:
        """Fetch and normalize jobs from this source."""
        pass
