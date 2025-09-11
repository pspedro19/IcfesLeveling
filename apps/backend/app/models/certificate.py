from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import uuid

class Certificate(Base):
    __tablename__ = "certificates"
    __table_args__ = {'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    unit_number = Column(Integer, nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    battle_id = Column(UUID(as_uuid=True), ForeignKey("battles.id"), nullable=False)
    certificate_data = Column(JSON, nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="certificates")
    subject = relationship("Subject")
    battle = relationship("Battle")
    
    def __repr__(self):
        return f"<Certificate(id={self.id}, user_id={self.user_id}, unit={self.unit_number})>"
    
    def get_certificate_title(self) -> str:
        """Get certificate title from data"""
        return self.certificate_data.get("title", f"Certificado - Unidad {self.unit_number}")
    
    def get_achievement_text(self) -> str:
        """Get achievement text from data"""
        return self.certificate_data.get("achievement", "Dominio demostrado")
    
    def get_completion_date(self) -> str:
        """Get completion date from data"""
        return self.certificate_data.get("completion_date", self.generated_at.isoformat())
    
    def get_battle_performance(self) -> dict:
        """Get battle performance data"""
        return self.certificate_data.get("battle_performance", {})
    
    def is_valid(self) -> bool:
        """Check if certificate is valid"""
        required_fields = ["title", "subject", "unit_number", "student_name", "completion_date"]
        return all(field in self.certificate_data for field in required_fields) 