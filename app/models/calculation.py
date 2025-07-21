from sqlalchemy import Column, Integer, Float, String, ForeignKey, Enum, func, DateTime
from sqlalchemy.orm import relationship
from app.db import Base
import enum

class CalculationType(str, enum.Enum):
    Add = "Add"
    Subtract = "Subtract"
    Multiply = "Multiply"
    Divide = "Divide"

class Calculation(Base):
    __tablename__ = "calculations"

    id = Column(Integer, primary_key=True, index=True)
    a = Column(Float, nullable=False)
    b = Column(Float, nullable=False)
    type = Column(Enum(CalculationType), nullable=False)
    # Optionally store result, or compute on demand via @property
    result = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # If you want to link to a user:
    # user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    # user = relationship("User", back_populates="calculations")
