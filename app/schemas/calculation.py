# app/schemas/calculation.py

from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from app.models.calculation import CalculationType

class CalculationCreate(BaseModel):
    a: float = Field(..., description="First operand")
    b: float = Field(..., description="Second operand")
    type: CalculationType

    @field_validator("b")
    def no_zero_divide(cls, v, info):
        # info.data holds the other fields, including type
        if info.data.get("type") == CalculationType.Divide and v == 0:
            raise ValueError("Division by zero is not allowed")
        return v

class CalculationRead(BaseModel):
    id: int
    a: float
    b: float
    type: CalculationType
    result: float
    created_at: datetime

    model_config = {
        "from_attributes": True
    }
