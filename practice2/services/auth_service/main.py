from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta
from database import Base, engine, get_db, User, RevokedToken
from models import RegisterRequest, LoginRequest, ValidateRequest, LogoutRequest
import os

app = FastAPI(title="Auth Service")
Base.metadata.create_all(bind=engine)

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=400, detail="Пользователь уже существует")
    user = User(
        username=req.username,
        hashed_password=pwd_context.hash(req.password),
        role=req.role
    )
    db.add(user)
    db.commit()
    return {"message": "Пользователь зарегистрирован", "username": req.username, "role": req.role}

@app.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not pwd_context.verify(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Неверные учётные данные")
    payload = {
        "sub": user.username,
        "role": user.role,
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}

@app.post("/validate")
def validate(req: ValidateRequest, db: Session = Depends(get_db)):
    if db.query(RevokedToken).filter(RevokedToken.token == req.token).first():
        raise HTTPException(status_code=401, detail="Токен отозван")
    try:
        payload = jwt.decode(req.token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"valid": True, "username": payload["sub"], "role": payload["role"]}
    except JWTError:
        raise HTTPException(status_code=401, detail="Токен недействителен")

@app.post("/logout")
def logout(req: LogoutRequest, db: Session = Depends(get_db)):
    db.add(RevokedToken(token=req.token))
    db.commit()
    return {"message": "Токен отозван"}