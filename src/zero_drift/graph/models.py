"""Graph Engine Data Models."""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

VALID_STATUSES = ["PENDING", "IN_PROGRESS", "COMPLETED", "VERIFIED", "FAILED"]

VALID_TRANSITIONS = {
    "PENDING": ["IN_PROGRESS", "FAILED"],
    "IN_PROGRESS": ["COMPLETED", "FAILED", "PENDING"],
    "COMPLETED": ["VERIFIED", "IN_PROGRESS"],
    "VERIFIED": ["PENDING"],
    "FAILED": ["PENDING"]
}

@dataclass
class Node:
    id: Optional[int] = None
    name: str = ""
    type: str = "TASK"
    status: str = "PENDING"
    content_hash: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Edge:
    id: Optional[int] = None
    source_id: int = 0
    target_id: int = 0
    relation_type: str = "DEPENDS_ON"
