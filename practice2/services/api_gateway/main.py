from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import os

app = FastAPI(title="API Gateway")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth_service:8001")

class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "user"

class LoginRequest(BaseModel):
    username: str
    password: str

class ValidateRequest(BaseModel):
    token: str

class LogoutRequest(BaseModel):
    token: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/auth/register")
async def register(req: RegisterRequest):
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{AUTH_SERVICE_URL}/register", json=req.model_dump())
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.json())
    return r.json()

@app.post("/auth/login")
async def login(req: LoginRequest):
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{AUTH_SERVICE_URL}/login", json=req.model_dump())
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.json())
    return r.json()

@app.post("/auth/validate")
async def validate(req: ValidateRequest):
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{AUTH_SERVICE_URL}/validate", json=req.model_dump())
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.json())
    return r.json()

@app.post("/auth/logout")
async def logout(req: LogoutRequest):
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{AUTH_SERVICE_URL}/logout", json=req.model_dump())
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.json())
    return r.json()