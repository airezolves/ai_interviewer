"""Common database connector — shared across all services that need DB access."""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData

from shared.config import BaseAppSettings


# Naming convention for constraints (consistent across migrations)
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=NAMING_CONVENTION)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models."""
    metadata = metadata


class DatabaseManager:
    """Async database connection manager.
    
    Usage:
        db = DatabaseManager(settings.database_url)
        async with db.session() as session:
            result = await session.execute(...)
    """

    def __init__(self, database_url: str, echo: bool = False):
        self.engine = create_async_engine(
            database_url,
            echo=echo,
            pool_size=20,
            max_overflow=10,
            pool_pre_ping=True,
        )
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def session(self) -> AsyncSession:
        """Get a new async session."""
        return self.async_session()

    async def get_session(self):
        """Dependency injection for FastAPI."""
        async with self.async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def close(self):
        """Close the engine connection pool."""
        await self.engine.dispose()


# Singleton instance — initialized per service
_db_instance: DatabaseManager | None = None


def init_database(database_url: str, echo: bool = False) -> DatabaseManager:
    """Initialize the database manager singleton."""
    global _db_instance
    _db_instance = DatabaseManager(database_url, echo=echo)
    return _db_instance


def get_database() -> DatabaseManager:
    """Get the database manager instance."""
    if _db_instance is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _db_instance
