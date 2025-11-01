# from fastapi import FastAPI
# from app.db.database import get_db_connection

# app = FastAPI()

# # Test DB connection once at startup:a
# conn = get_db_connection()
# cursor = conn.cursor() if conn else None

# @app.get("/")
# def home():
#     if not cursor:
#         return {"error": "Database not connected"}

#     cursor.execute("SELECT NOW();")
#     result = cursor.fetchone()
#     return {"message": "Hello from FastAPI + Supabase!", "time": result["now"]}
from fastapi import FastAPI
from app.db.database import get_db_connection
from app.api.v1 import auth  
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

# ✅ Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Allow any origin
    allow_credentials=True,
    allow_methods=["*"],       # Allow GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],       # Allow all headers
)


# Include your auth endpoints
app.include_router(auth.router)

# Test DB connection once at startup
conn = get_db_connection()
cursor = conn.cursor() if conn else None

@app.get("/")
def home():
    if not cursor:
        return {"error": "Database not connected"}

    cursor.execute("SELECT NOW();")
    result = cursor.fetchone()
    return {"message": "Hello from FastAPI + Supabase!", "time": result["now"]}
