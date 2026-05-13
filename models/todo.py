from dataclasses import dataclass
from typing import Optional

@dataclass
class Todo:
    title: str
    id: Optional[int] = None
    project_id: Optional[int] = None
    description: Optional[str] = None
    status: str = "todo"  # 'todo' | 'doing' | 'done'
    priority: str = "medium"  # 'high' | 'medium' | 'low'
    due_date: Optional[str] = None
    created_at: Optional[str] = None
