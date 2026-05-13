from dataclasses import dataclass
from typing import Optional

@dataclass
class Tag:
    name: str
    id: Optional[int] = None
    color: str = "#4A90D9"
