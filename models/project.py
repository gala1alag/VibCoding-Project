from dataclasses import dataclass
from typing import Optional

@dataclass
class Project:
    name: str
    path: str
    type: str  # 'folder' | 'file'
    id: Optional[int] = None
    language: Optional[str] = None
    note: Optional[str] = None
    content: Optional[str] = None
    default_editor: Optional[str] = None
    created_at: Optional[str] = None
    last_opened_at: Optional[str] = None
