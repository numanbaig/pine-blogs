import uuid

from pydantic import BaseModel, Field

class BlogCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)

class BlogUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)

class Blog(BaseModel):
    id: uuid.UUID
    title: str
    content: str