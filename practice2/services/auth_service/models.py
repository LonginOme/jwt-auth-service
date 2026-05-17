from pydantic import BaseModel

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