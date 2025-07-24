from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class BaseDomainModel(BaseModel):
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None


class BasePersistenceModel(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    is_deleted: bool = False
