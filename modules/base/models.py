from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class BaseDomainModel(BaseModel):
    id: int = -100
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
