from sqlalchemy.ext.asyncio import AsyncSession

class BaseSQLAlchemyRepository:
    """Base repository class containing the database session."""
    def __init__(self, session: AsyncSession):
        self.session = session
