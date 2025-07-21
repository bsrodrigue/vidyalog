from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class InputBaseModel:
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass(frozen=True)
class RepositoryBaseModel:
    """
    Return Type from Repository Actions
    """

    id: int
    created_at: datetime
    updated_at: datetime
