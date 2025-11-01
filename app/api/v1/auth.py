from fastapi import APIRouter, HTTPException
from app.models.user_models import UserSignup
from app.db.database import get_db_connection

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup")
def signup_user(user: UserSignup):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if user already exists
    cursor.execute("SELECT * FROM user WHERE email = %s;", (user.Email,))
    existing_user = cursor.fetchone()

    if existing_user:
        conn.close()
        raise HTTPException(status_code=400, detail="User already exists with this email.")

    # Insert new user
    cursor.execute("""
        INSERT INTO user (name, email, country, province, city)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING *;
    """, (user.Name, user.Email, user.country, user.province, user.city))

    new_user = cursor.fetchone()
    conn.commit()
    conn.close()

    return {"message": "User signed up successfully!", "user": new_user}
