
from fastapi import APIRouter, HTTPException
from app.db.database import get_db_connection
from app.models.user_models import UserSignup,UserLogin
from app.utils.hash_util import hash_password, verify_password  # ✅ both imported

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ========================
# 🔹 SIGNUP ENDPOINT
# ========================
@router.post("/signup")
def signup_user(user: UserSignup):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cursor = conn.cursor()

    # Check if email already exists
    cursor.execute('SELECT * FROM "user" WHERE email = %s;', (user.email,))
    existing_user = cursor.fetchone()

    if existing_user:
        cursor.close()
        conn.close()
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists. Please log in or use a different email."
        )

    # ✅ Hash password
    hashed_pw = hash_password(user.password)

    # Insert new user
    cursor.execute(
        """
        INSERT INTO "user" (name, email, password, contact, province, city)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id, name, email, contact, province, city;
        """,
        (user.name, user.email, hashed_pw, user.contact, user.province, user.city)
    )

    new_user = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()

    return {"message": "User registered successfully!", "user": new_user}



@router.post("/login")
def login_user(user: UserLogin):   # ✅ expect JSON body
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cursor = conn.cursor()
    cursor.execute('SELECT * FROM "user" WHERE email = %s;', (user.email,))
    db_user = cursor.fetchone()

    if not db_user:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="No account found with this email.")

    if not verify_password(user.password, db_user["password"]):
        cursor.close()
        conn.close()
        raise HTTPException(status_code=401, detail="Incorrect password.")

    cursor.close()
    conn.close()

    return {
        "message": "Login successful!",
        "user": {
            "id": db_user["id"],
            "name": db_user["name"],
            "email": db_user["email"],
            "contact": db_user["contact"],
            "province": db_user["province"],
            "city": db_user["city"],
        }
    }