"""
FastAPI CRUD Microservice with JWT Authentication
A production-ready task management API.
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID, uuid4

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import jwt

# ── Configuration ──────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ── Logging ────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


# ── Models ─────────────────────────────────────────────
class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    priority: str = Field(default="medium", pattern="^(low|medium|high|critical)$")


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|critical)$")
    completed: Optional[bool] = None


class TaskOut(BaseModel):
    id: UUID
    title: str
    description: str
    priority: str
    completed: bool
    created_at: datetime
    updated_at: datetime


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── In-memory storage (replace with DB in production) ──
tasks_db: dict[UUID, dict] = {}
users_db = {"admin": {"password": "admin123", "role": "admin"}}

# ── Auth helpers ───────────────────────────────────────
security = HTTPBearer()


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Create a JWT access token with expiry."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Verify JWT token and return payload."""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ── Application ────────────────────────────────────────
app = FastAPI(
    title="Task Manager API",
    description="Production-ready CRUD microservice with JWT auth",
    version="1.0.0",
)


@app.post("/auth/login", response_model=TokenResponse)
def login(data: UserLogin):
    """Authenticate user and return JWT token."""
    user = users_db.get(data.username)
    if not user or user["password"] != data.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": data.username, "role": user["role"]})
    logger.info("User %s logged in", data.username)
    return TokenResponse(access_token=token)


@app.post("/tasks", response_model=TaskOut, status_code=201)
def create_task(task: TaskCreate, user: dict = Depends(verify_token)):
    """Create a new task."""
    task_id = uuid4()
    now = datetime.utcnow()
    record = {
        "id": task_id,
        "title": task.title,
        "description": task.description,
        "priority": task.priority,
        "completed": False,
        "created_at": now,
        "updated_at": now,
        "owner": user["sub"],
    }
    tasks_db[task_id] = record
    logger.info("Task %s created by %s", task_id, user["sub"])
    return TaskOut(**record)


@app.get("/tasks", response_model=list[TaskOut])
def list_tasks(
    completed: Optional[bool] = None,
    priority: Optional[str] = None,
    user: dict = Depends(verify_token),
):
    """List all tasks with optional filters."""
    results = list(tasks_db.values())
    if completed is not None:
        results = [t for t in results if t["completed"] == completed]
    if priority:
        results = [t for t in results if t["priority"] == priority]
    return [TaskOut(**t) for t in results]


@app.get("/tasks/{task_id}", response_model=TaskOut)
def get_task(task_id: UUID, user: dict = Depends(verify_token)):
    """Get a specific task by ID."""
    task = tasks_db.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskOut(**task)


@app.put("/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: UUID, update: TaskUpdate, user: dict = Depends(verify_token)):
    """Update an existing task."""
    task = tasks_db.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    for field, value in update.model_dump(exclude_unset=True).items():
        task[field] = value
    task["updated_at"] = datetime.utcnow()
    logger.info("Task %s updated by %s", task_id, user["sub"])
    return TaskOut(**task)


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: UUID, user: dict = Depends(verify_token)):
    """Delete a task."""
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    del tasks_db[task_id]
    logger.info("Task %s deleted by %s", task_id, user["sub"])


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "tasks_count": len(tasks_db)}
