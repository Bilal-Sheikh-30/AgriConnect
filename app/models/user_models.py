from pydantic import BaseModel, EmailStr, Field
from typing import Annotated
from typing import Optional

class UserSignup(BaseModel):
    name: Annotated[str, Field(min_length=2)]
    email: EmailStr
    password: Annotated[str, Field(min_length=2)]
    contact: str
    province: Annotated[str, Field(min_length=2)]
    city: Annotated[str, Field(min_length=2)]

class UserLogin(BaseModel):
    email: EmailStr
    password: str




class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    contact: Optional[str] = None
    city: Optional[str] = None    