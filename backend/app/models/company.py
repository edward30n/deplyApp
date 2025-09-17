from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Boolean, DateTime
from sqlalchemy.orm import relationship

from app.database.session import Base

class Company(Base):
    __tablename__ = "companies"

    # Coincide exactamente con la estructura de la BD
    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    invite_code = Column(String(50), unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relaciones (usando strings para evitar circular imports)
    users = relationship("User", back_populates="company")
    
    def __repr__(self):
        return f"<Company(id={self.id}, name='{self.name}')>"
