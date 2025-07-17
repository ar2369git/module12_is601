# main.py

import logging
import uvicorn
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, field_validator

from sqlalchemy.orm import Session

from app.operations import add, subtract, multiply, divide
from app.db import engine, Base, get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserRead
from app.security import hash_password, verify_password  # verify_password is available if you later add login

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Create all tables on startup
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

# Setup templates directory
templates = Jinja2Templates(directory="templates")

#
# Calculator Pydantic models & routes (unchanged)
#

class OperationRequest(BaseModel):
    a: float = Field(..., description="The first number")
    b: float = Field(..., description="The second number")

    @field_validator("a", "b")
    def validate_numbers(cls, v):
        if not isinstance(v, (int, float)):
            raise ValueError("Both a and b must be numbers.")
        return v

class OperationResponse(BaseModel):
    result: float = Field(..., description="The result of the operation")

class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTPException on {request.url.path}: {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_messages = "; ".join(f"{err['loc'][-1]}: {err['msg']}" for err in exc.errors())
    logger.error(f"ValidationError on {request.url.path}: {error_messages}")
    return JSONResponse(status_code=400, content={"error": error_messages})

@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/add", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def add_route(operation: OperationRequest):
    try:
        result = add(operation.a, operation.b)
        return OperationResponse(result=result)
    except Exception as e:
        logger.error(f"Add Operation Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/subtract", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def subtract_route(operation: OperationRequest):
    try:
        result = subtract(operation.a, operation.b)
        return OperationResponse(result=result)
    except Exception as e:
        logger.error(f"Subtract Operation Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/multiply", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def multiply_route(operation: OperationRequest):
    try:
        result = multiply(operation.a, operation.b)
        return OperationResponse(result=result)
    except Exception as e:
        logger.error(f"Multiply Operation Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/divide", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def divide_route(operation: OperationRequest):
    try:
        result = divide(operation.a, operation.b)
        return OperationResponse(result=result)
    except ValueError as e:
        logger.error(f"Divide Operation Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Divide Operation Internal Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

#
# New User registration endpoint
#

@app.post("/register", response_model=UserRead, responses={400: {"model": ErrorResponse}})
async def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    # Ensure username/email are unique
    exists = db.query(User).filter(
        (User.username == payload.username) |
        (User.email == payload.email)
    ).first()
    if exists:
        logger.warning("Attempt to register with existing username or email")
        raise HTTPException(status_code=400, detail="Username or email already registered")

    # Hash the incoming password
    hashed_pw = hash_password(payload.password)

    # Create and save the user
    user = User(username=payload.username, email=payload.email, password_hash=hashed_pw)
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info(f"Registered new user: {user.username}")
    return UserRead.from_orm(user)

# Entry point for local runs; ignored by coverage
if __name__ == "__main__":  # pragma: no cover
    uvicorn.run(app, host="127.0.0.1", port=8000)
