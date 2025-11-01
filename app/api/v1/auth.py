from fastapi import APIRouter, HTTPException,Depends
from app.db.database import get_db_connection
from app.models.user_models import UserSignup,UserLogin,UserUpdate
from app.utils.hash_util import hash_password, verify_password  # ✅ both imported
from app.utils.jwt_util import create_access_token
from app.utils.jwt_util import get_current_user

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

    # return {"message": "User registered successfully!", "user": new_user}
    token = create_access_token({"user_id": new_user["id"]})
    return {"message": "User registered successfully!", "user": new_user, "access_token": token}



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

    token = create_access_token({"user_id": db_user["id"]})
    cursor.close()
    conn.close()

  
    return {
        "message": "Login successful!",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": db_user["id"],
            "name": db_user["name"],
            "email": db_user["email"],
            "contact": db_user["contact"],
            "province": db_user["province"],
            "city": db_user["city"],
        }
    }


@router.put("/edit")
def edit_user(user_update: UserUpdate, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cursor = conn.cursor()

    # Check if new email is already taken by another user
    if user_update.email:
        cursor.execute('SELECT id FROM "user" WHERE email = %s AND id != %s;', (user_update.email, current_user["id"]))
        existing = cursor.fetchone()
        if existing:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=409, detail="This email is already used by another account.")

    # Build update dynamically
    update_fields = []
    update_values = []

    if user_update.name:
        update_fields.append("name = %s")
        update_values.append(user_update.name)
    if user_update.email:
        update_fields.append("email = %s")
        update_values.append(user_update.email)
    if user_update.contact:
        update_fields.append("contact = %s")
        update_values.append(user_update.contact)
    if user_update.city:
        update_fields.append("city = %s")
        update_values.append(user_update.city)

    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update provided.")

    update_values.append(current_user["id"])  # for WHERE clause

    query = f'UPDATE "user" SET {", ".join(update_fields)} WHERE id = %s RETURNING id, name, email, contact, city;'
    cursor.execute(query, tuple(update_values))
    updated_user = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()

    return {"message": "User updated successfully!", "user": updated_user}