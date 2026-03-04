from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from ..core.database import Base

class RevokedToken(Base):
    __tablename__ = "revoked_tokens"

    jti = Column(String, primary_key=True, index=True)
    revoked_at = Column(DateTime, server_default=func.now(), nullable=False)
