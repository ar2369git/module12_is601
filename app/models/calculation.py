# app/models/calculation.py
from sqlalchemy import Column, Integer, Enum, Float, ForeignKey
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
    result = Column(Float, nullable=True)
    # optional user_id example:
    # user_id = Column(Integer, ForeignKey("users.id"))
