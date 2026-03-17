from pydantic import BaseModel, Field


class SignupRequest(BaseModel):
    email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$")
    password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$")
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
