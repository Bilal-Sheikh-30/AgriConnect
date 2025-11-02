
from fastapi import FastAPI
from app.db.database import get_db_connection
from app.api.v1 import auth,chatbot, resource, marketplace
from app.api.v1 import auth,chatbot, resource,rentals
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

# Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       
    allow_credentials=True,
    allow_methods=["*"],       
    allow_headers=["*"],       
)


# Include  auth endpoints
app.include_router(auth.router)
app.include_router(chatbot.router)
app.include_router(rentals.router)

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

app.include_router(resource.router, prefix="/api/v1/resource", tags=["Resource"])
app.include_router(marketplace.router, prefix="/api/v1", tags=["marketplace"])