from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)

class UserRead(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: str

    class Config:
        orm_mode = True
