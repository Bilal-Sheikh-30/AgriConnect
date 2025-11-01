# from pydantic import BaseModel, EmailStr, Field
# from typing import Annotated

# class UserSignup(BaseModel):
#     Name: Annotated[str, Field(min_length=2)]
#     Email: EmailStr
#     Password: Annotated[str, Field(min_length=6)]
#     contact: int
#     province: Annotated[str, Field(min_length=2)]
#     city: Annotated[str, Field(min_length=2)]
from pydantic import BaseModel, EmailStr, Field
from typing import Annotated

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