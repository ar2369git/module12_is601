from pydantic import BaseModel, Field, validator
from datetime import datetime
from app.models.calculation import CalculationType

class CalculationCreate(BaseModel):
    a: float = Field(..., description="First operand")
    b: float = Field(..., description="Second operand")
    type: CalculationType

    @validator("b")
    def no_zero_divide(cls, v, values):
        if values.get("type") == CalculationType.Divide and v == 0:
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
