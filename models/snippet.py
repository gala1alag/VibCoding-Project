from dataclasses import dataclass
from typing import Optional

@dataclass
class Snippet:
    title: str
    id: Optional[int] = None
    language: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    project_id: Optional[int] = None
    created_at: Optional[str] = None
