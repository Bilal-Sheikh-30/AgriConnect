from fastapi import FastAPI
from app.db.database import get_db_connection

app = FastAPI()

# Test DB connection once at startup:a
conn = get_db_connection()
cursor = conn.cursor() if conn else None

@app.get("/")
def home():
    if not cursor:
        return {"error": "Database not connected"}

    cursor.execute("SELECT NOW();")
    result = cursor.fetchone()
    return {"message": "Hello from FastAPI + Supabase!", "time": result["now"]}
