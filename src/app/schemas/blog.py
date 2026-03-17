import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BlogCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)


class BlogUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)


class BlogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
    user_id: uuid.UUID


class PaginatedBlogsResponse(BaseModel):
    items: list[BlogResponse]
    total: int