# main.py
import logging
import uuid
import uvicorn
from fastapi import FastAPI, HTTPException, Request, Depends, Header
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.operations import add, subtract, multiply, divide
from app.db import get_db, init_db
from app.models.user import User
from app.models.calculation import Calculation, CalculationType
from app.schemas.user import UserCreate, UserRead, UserLogin, TokenResponse
from app.schemas.calculation import (
    CalculationCreate,
    CalculationRead,
    CalculationUpdate,
)
from app.security import hash_password, verify_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Simple in-memory token store (token -> user_id)
TOKENS: dict[str, int] = {}


@app.on_event("startup")
def startup():
    init_db()


@app.get("/", response_class=HTMLResponse)
def homepage():
    return """
    <html>
      <body>
        <h1>Hello World</h1>
        <p>See /docs for API.</p>
      </body>
    </html>
    """


# ----- Legacy calculator operation endpoints (kept so existing tests still pass) -----
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


@app.post("/add", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def add_route(operation: OperationRequest):
    try:
        return OperationResponse(result=add(operation.a, operation.b))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/subtract", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def subtract_route(operation: OperationRequest):
    try:
        return OperationResponse(result=subtract(operation.a, operation.b))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/multiply", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def multiply_route(operation: OperationRequest):
    try:
        return OperationResponse(result=multiply(operation.a, operation.b))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/divide", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def divide_route(operation: OperationRequest):
    try:
        return OperationResponse(result=divide(operation.a, operation.b))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")


# ----- User Registration & Login -----
@app.post("/users/register", response_model=UserRead, responses={400: {"model": ErrorResponse}})
async def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    exists = (
        db.query(User)
        .filter((User.username == payload.username) | (User.email == payload.email))
        .first()
    )
    if exists:
        raise HTTPException(status_code=400, detail="Username or email already registered")

    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserRead.from_orm(user)


@app.post("/users/login", response_model=TokenResponse, responses={400: {"model": ErrorResponse}})
async def login_user(payload: UserLogin, db: Session = Depends(get_db)):
    user = (
        db.query(User)
        .filter(
            (User.username == payload.username_or_email)
            | (User.email == payload.username_or_email)
        )
        .first()
    )
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    token = str(uuid.uuid4())
    TOKENS[token] = user.id
    return TokenResponse(token=token, user=UserRead.from_orm(user))


def get_current_user(
    authorization: str = Header(None), db: Session = Depends(get_db)
) -> User:
    """
    Expect header: Authorization: Bearer <token>
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    token = authorization.split()[1]
    user_id = TOKENS.get(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


# ----- Calculation CRUD (protected) -----
@app.post(
    "/calculations",
    response_model=CalculationRead,
    responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}},
)
def create_calculation(
    payload: CalculationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),  # noqa: unused (for future extension)
):
    # Compute result
    if payload.type == CalculationType.Add:
        res = add(payload.a, payload.b)
    elif payload.type == CalculationType.Subtract:
        res = subtract(payload.a, payload.b)
    elif payload.type == CalculationType.Multiply:
        res = multiply(payload.a, payload.b)
    else:
        res = divide(payload.a, payload.b)

    calc = Calculation(a=payload.a, b=payload.b, type=payload.type, result=res)
    db.add(calc)
    db.commit()
    db.refresh(calc)
    return calc


@app.get(
    "/calculations",
    response_model=list[CalculationRead],
    responses={401: {"model": ErrorResponse}},
)
def list_calculations(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return db.query(Calculation).order_by(Calculation.id).all()


@app.get(
    "/calculations/{calc_id}",
    response_model=CalculationRead,
    responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}},
)
def get_calculation(
    calc_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    calc = db.get(Calculation, calc_id)
    if not calc:
        raise HTTPException(status_code=404, detail="Calculation not found")
    return calc


@app.put(
    "/calculations/{calc_id}",
    response_model=CalculationRead,
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}},
)
def update_calculation(
    calc_id: int,
    payload: CalculationUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    calc = db.get(Calculation, calc_id)
    if not calc:
        raise HTTPException(status_code=404, detail="Calculation not found")

    # Recalculate
    if payload.type == CalculationType.Add:
        res = add(payload.a, payload.b)
    elif payload.type == CalculationType.Subtract:
        res = subtract(payload.a, payload.b)
    elif payload.type == CalculationType.Multiply:
        res = multiply(payload.a, payload.b)
    else:
        res = divide(payload.a, payload.b)

    calc.a = payload.a
    calc.b = payload.b
    calc.type = payload.type
    calc.result = res
    db.commit()
    db.refresh(calc)
    return calc


@app.delete(
    "/calculations/{calc_id}",
    status_code=204,
    responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}},
)
def delete_calculation(
    calc_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    calc = db.get(Calculation, calc_id)
    if not calc:
        raise HTTPException(status_code=404, detail="Calculation not found")
    db.delete(calc)
    db.commit()
    return None


if __name__ == "__main__":  # pragma: no cover
    uvicorn.run(app, host="127.0.0.1", port=8000)
