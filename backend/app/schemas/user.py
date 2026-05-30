from pydantic import BaseModel, EmailStr

class UserRegister(BaseModel):
    email: str
    password: str
    display_name: str = ""

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    display_name: str
    model_config = {"from_attributes": True}

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
