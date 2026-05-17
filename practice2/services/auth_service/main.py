from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta
from database import Base, engine, get_db, User, RevokedToken
from models import RegisterRequest, LoginRequest, ValidateRequest, LogoutRequest
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time
import os

app = FastAPI(title="Auth Service")
Base.metadata.create_all(bind=engine)

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Метрики
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Количество HTTP запросов",
    ["method", "endpoint", "status"]
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "Время ответа в секундах",
    ["endpoint"]
)
TOKENS_ISSUED = Counter(
    "tokens_issued_total",
    "Количество выданных токенов"
)
TOKENS_VALIDATED = Counter(
    "tokens_validated_total",
    "Количество валидаций токенов",
    ["result"]
)
USERS_REGISTERED = Counter(
    "users_registered_total",
    "Количество зарегистрированных пользователей"
)

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    start = time.time()
    if db.query(User).filter(User.username == req.username).first():
        REQUEST_COUNT.labels("POST", "/register", "400").inc()
        raise HTTPException(status_code=400, detail="Пользователь уже существует")
    user = User(
        username=req.username,
        hashed_password=pwd_context.hash(req.password),
        role=req.role
    )
    db.add(user)
    db.commit()
    USERS_REGISTERED.inc()
    REQUEST_COUNT.labels("POST", "/register", "200").inc()
    REQUEST_LATENCY.labels("/register").observe(time.time() - start)
    return {"message": "Пользователь зарегистрирован", "username": req.username, "role": req.role}

@app.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    start = time.time()
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not pwd_context.verify(req.password, user.hashed_password):
        REQUEST_COUNT.labels("POST", "/login", "401").inc()
        raise HTTPException(status_code=401, detail="Неверные учётные данные")
    payload = {
        "sub": user.username,
        "role": user.role,
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    TOKENS_ISSUED.inc()
    REQUEST_COUNT.labels("POST", "/login", "200").inc()
    REQUEST_LATENCY.labels("/login").observe(time.time() - start)
    return {"access_token": token, "token_type": "bearer"}

@app.post("/validate")
def validate(req: ValidateRequest, db: Session = Depends(get_db)):
    start = time.time()
    if db.query(RevokedToken).filter(RevokedToken.token == req.token).first():
        TOKENS_VALIDATED.labels("revoked").inc()
        REQUEST_COUNT.labels("POST", "/validate", "401").inc()
        raise HTTPException(status_code=401, detail="Токен отозван")
    try:
        payload = jwt.decode(req.token, SECRET_KEY, algorithms=[ALGORITHM])
        TOKENS_VALIDATED.labels("valid").inc()
        REQUEST_COUNT.labels("POST", "/validate", "200").inc()
        REQUEST_LATENCY.labels("/validate").observe(time.time() - start)
        return {"valid": True, "username": payload["sub"], "role": payload["role"]}
    except JWTError:
        TOKENS_VALIDATED.labels("invalid").inc()
        REQUEST_COUNT.labels("POST", "/validate", "401").inc()
        raise HTTPException(status_code=401, detail="Токен недействителен")

@app.post("/logout")
def logout(req: LogoutRequest, db: Session = Depends(get_db)):
    start = time.time()
    db.add(RevokedToken(token=req.token))
    db.commit()
    REQUEST_COUNT.labels("POST", "/logout", "200").inc()
    REQUEST_LATENCY.labels("/logout").observe(time.time() - start)
    return {"message": "Токен отозван"}