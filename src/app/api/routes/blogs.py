import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.database import get_db
from app.models.blogs import Blog
from app.models.user import User
from app.schemas.blog import BlogCreate, BlogUpdate

router = APIRouter()


@router.post("/", response_model=Blog)
async def create_blog(
    blog: BlogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_blog = Blog(
        title=blog.title,
        content=blog.content,
        user_id=current_user.id,
    )
    db.add(db_blog)
    await db.commit()
    await db.refresh(db_blog)
    return db_blog


@router.get("/", response_model=list[Blog])
async def get_blogs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Blog))
    return result.scalars().all()


@router.get("/{blog_id}", response_model=Blog)
async def get_blog(blog_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Blog).where(Blog.id == blog_id))
    return result.scalar_one_or_none()


@router.put("/{blog_id}", response_model=Blog)
async def update_blog(blog_id: uuid.UUID, blog: BlogUpdate, db: AsyncSession = Depends(get_db)):
    db_blog = await db.get(Blog, blog_id)
    if not db_blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    db_blog.title = blog.title
    db_blog.content = blog.content
    await db.commit()
    await db.refresh(db_blog)
    return db_blog

@router.delete("/{blog_id}", response_model=Blog)
async def delete_blog(blog_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    db_blog = await db.get(Blog, blog_id)
    if not db_blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    await db.delete(db_blog)
    await db.commit()
    return db_blog