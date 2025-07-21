# main.py
import logging
import uvicorn
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.operations import add, subtract, multiply, divide
from app.db import engine, Base, get_db, init_db
from app.models.user import User
from app.models.calculation import Calculation
from app.schemas.user import UserCreate, UserRead
from app.security import hash_password, verify_password
from app.db import get_db, init_db


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/", response_class=HTMLResponse)
def homepage():
    return """
    <html>
      <body>
        <h1>Hello World</h1>
        <input id="a" type="number" />
        <input id="b" type="number" />
        <button id="add">Add</button>
        <button id="subtract">Subtract</button>
        <button id="multiply">Multiply</button>
        <button id="divide">Divide</button>
        <div id="result"></div>
        <script>
          async function doOp(endpoint) {
            const a = parseFloat(document.getElementById('a').value);
            const b = parseFloat(document.getElementById('b').value);
            const resp = await fetch('/' + endpoint, {
              method: 'POST',
              headers: {'Content-Type': 'application/json'},
              body: JSON.stringify({a, b})
            });
            const data = await resp.json();
            const text = resp.ok ? `Calculation Result: ${data.result}` : `Error: ${data.error}`;
            document.getElementById('result').textContent = text;
          }
          document.getElementById('add').onclick = () => doOp('add');
          document.getElementById('subtract').onclick = () => doOp('subtract');
          document.getElementById('multiply').onclick = () => doOp('multiply');
          document.getElementById('divide').onclick = () => doOp('divide');
        </script>
      </body>
    </html>
    """



templates = Jinja2Templates(directory="templates")

class OperationRequest(BaseModel):
    a: float
    b: float

    @field_validator("a", "b")
    def validate_numbers(cls, v):
        if not isinstance(v, (int, float)):
            raise ValueError("Both a and b must be numbers.")
        return v

class OperationResponse(BaseModel):
    result: float

class ErrorResponse(BaseModel):
    error: str

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
        logger.error(f"Add Operation Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/subtract", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def subtract_route(operation: OperationRequest):
    try:
        return OperationResponse(result=subtract(operation.a, operation.b))
    except Exception as e:
        logger.error(f"Subtract Operation Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/multiply", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def multiply_route(operation: OperationRequest):
    try:
        return OperationResponse(result=multiply(operation.a, operation.b))
    except Exception as e:
        logger.error(f"Multiply Operation Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/divide", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def divide_route(operation: OperationRequest):
    try:
        return OperationResponse(result=divide(operation.a, operation.b))
    except ValueError as e:
        logger.error(f"Divide Operation Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Divide Operation Internal Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/register", response_model=UserRead, responses={400: {"model": ErrorResponse}})
async def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    exists = db.query(User).filter(
        (User.username == payload.username) | (User.email == payload.email)
    ).first()
    if exists:
        logger.warning("Attempt to register with existing username or email")
        raise HTTPException(status_code=400, detail="Username or email already registered")

    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f"Registered new user: {user.username}")
    return UserRead.from_orm(user)

if __name__ == "__main__":  # pragma: no cover
    uvicorn.run(app, host="127.0.0.1", port=8000)
