from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.auth import router as auth_router
from app.api.routes.blogs import router as blogs_router
from app.db.database import Base, engine, get_db
from app.models.blogs import Blog  # noqa: F401 - register model with Base
from app.models.user import User  # noqa: F401 - register model with Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(blogs_router, prefix="/blogs", tags=["blogs"])

@app.get("/")
def read_root():
    return {"message": "Hello World"}


@app.get("/health/db")
async def check_db(db: AsyncSession = Depends(get_db)):
    """Verify database connection by running a simple query."""
    result = await db.execute(text("SELECT 1"))
    result.scalar()
    return {"status": "connected", "database": "pine-blogs"}
