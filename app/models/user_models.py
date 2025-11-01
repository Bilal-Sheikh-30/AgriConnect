from pydantic import BaseModel, EmailStr, constr

class UserSignup(BaseModel):
    Name: constr(strip_whitespace=True, min_length=2)
    Email: EmailStr
    country: int
    province: constr(strip_whitespace=True, min_length=2)
    city: constr(strip_whitespace=True, min_length=2)
