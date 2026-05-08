import re
from pydantic import BaseModel, EmailStr, field_validator


# ── Password policy ──────────────────────────────────────────────────────
_PASSWORD_MIN_LEN   = 8
_PASSWORD_UPPERCASE = re.compile(r"[A-Z]")
_PASSWORD_DIGIT     = re.compile(r"\d")
_PASSWORD_SPECIAL   = re.compile(r"[!@#$%^&*(),.?\":{}|<>_\-]")


def validate_password(value: str) -> str:
    errors = []
    if len(value) < _PASSWORD_MIN_LEN:
        errors.append(f"must be at least {_PASSWORD_MIN_LEN} characters")
    if not _PASSWORD_UPPERCASE.search(value):
        errors.append("must contain at least one uppercase letter")
    if not _PASSWORD_DIGIT.search(value):
        errors.append("must contain at least one digit")
    if not _PASSWORD_SPECIAL.search(value):
        errors.append("must contain at least one special character")
    if errors:
        raise ValueError("; ".join(errors))
    return value


# ── Request schemas ──────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

    @field_validator("username")
    @classmethod
    def username_valid(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3 or len(v) > 50:
            raise ValueError("username must be between 3 and 50 characters")
        if not re.match(r"^[a-zA-Z0-9_.-]+$", v):
            raise ValueError("username may only contain letters, digits, _, ., -")
        return v

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return validate_password(v)


class LoginRequest(BaseModel):
    username: str   # acepta username o email (se valida en el servicio)
    password: str


# ── Response schemas ─────────────────────────────────────────────────────
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool

    model_config = {"from_attributes": True}
