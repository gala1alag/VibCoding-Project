from dataclasses import dataclass
from typing import Optional

@dataclass
class StudyLog:
    duration_minutes: int
    date: str
    id: Optional[int] = None
    project_id: Optional[int] = None
    created_at: Optional[str] = None
