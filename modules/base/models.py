from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class BaseModel:
    id: Optional[int]
    created_at: datetime
    updated_at: datetime


@dataclass
class InputBaseModel:
    id: Optional[int]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


@dataclass(frozen=True)
class RepositoryBaseModel:
    """
    Return Type from Repository Actions
    """

    id: int
    created_at: datetime
    updated_at: datetime
