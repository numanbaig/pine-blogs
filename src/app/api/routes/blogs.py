import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.database import get_db
from app.models.blogs import Blog
from app.models.user import User
from app.schemas.blog import BlogCreate, BlogResponse, BlogUpdate, PaginatedBlogsResponse

router = APIRouter()


@router.post("/", response_model=BlogResponse)
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


@router.get("/", response_model=PaginatedBlogsResponse)
async def get_blogs(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    author_id: uuid.UUID | None = Query(None),
):
    count_stmt = select(func.count()).select_from(Blog)
    if author_id is not None:
        count_stmt = count_stmt.where(Blog.user_id == author_id)
    count_result = await db.execute(count_stmt)
    total = count_result.scalar()

    stmt = select(Blog)
    if author_id is not None:
        stmt = stmt.where(Blog.user_id == author_id)
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    items = result.scalars().all()

    return PaginatedBlogsResponse(items=items, total=total)


@router.get("/{blog_id}", response_model=BlogResponse)
async def get_blog(blog_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Blog).where(Blog.id == blog_id))
    db_blog = result.scalar_one_or_none()
    if not db_blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")
    return db_blog


@router.put("/{blog_id}", response_model=BlogResponse)
async def update_blog(
    blog_id: uuid.UUID,
    blog: BlogUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Blog).where(Blog.id == blog_id))
    db_blog = result.scalar_one_or_none()
    if not db_blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")
    if db_blog.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this blog")
    db_blog.title = blog.title
    db_blog.content = blog.content
    await db.commit()
    await db.refresh(db_blog)
    return db_blog


@router.delete("/{blog_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_blog(
    blog_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Blog).where(Blog.id == blog_id))
    db_blog = result.scalar_one_or_none()
    if not db_blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")
    if db_blog.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this blog")
    await db.delete(db_blog)
    await db.commit()