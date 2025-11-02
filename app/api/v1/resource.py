from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from app.db.database import get_db_connection
from app.utils.jwt_util import get_current_user
import cloudinary.uploader
import uuid
import os
import psycopg2.extras
from dotenv import load_dotenv
import psycopg2.extras

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

router = APIRouter(prefix="/resource", tags=["Resource"])

from fastapi import HTTPException
import psycopg2.extras

@router.get("/available")
def get_available_resources():
    """
    Get all resources where status = 'available', 
    including owner's name, province, and city
    """
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        # Use RealDictCursor to get dicts
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Join Resource with User to get owner info
        cursor.execute('''
            SELECT r.id, r.title, r.category, r.image, r.rent_per_hour, r.status,
                   r.owner, u.name AS owner_name, u.province AS owner_province, u.city AS owner_city
            FROM "Resource" r
            JOIN "user" u ON r.owner = u.id
            WHERE r.status = %s;
        ''', ("available",))

        resources = cursor.fetchall()  # List of dicts

        # Convert Decimal to float for rent_per_hour
        for r in resources:
            r["rent_per_hour"] = float(r["rent_per_hour"])

        cursor.close()
        conn.close()

        if not resources:
            return {"message": "No available resources found.", "resources": []}

        return {"resources": resources}

    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create")
async def create_resource(
    title: str = Form(...),
    category: str = Form(...),
    rent_per_hour: float = Form(...),
    image: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cursor = conn.cursor()

    # Upload image to Cloudinary
    try:
        upload_result = cloudinary.uploader.upload(image.file, folder="resources")
        image_url = upload_result.get("secure_url")
    except Exception as e:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")

    # Insert resource into DB
    cursor.execute(
        """
        INSERT INTO "Resource" (title, category, image, "rent_per_hour", status, owner)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id, title, category, image, "rent_per_hour", status, owner;
        """,
        (title, category, image_url, rent_per_hour, "available", current_user["id"])
    )
    
    new_resource = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()

    return {"message": "Resource created successfully!", "resource": new_resource}


@router.get("/my-resources")
async def get_my_resources(current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        # Use RealDictCursor to get dict results
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute(
            """
            SELECT id, title, category, image, "rent_per_hour", status, owner
            FROM "Resource"
            WHERE owner = %s
            """,
            (current_user["id"],)
        )
        resources = cursor.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch resources: {str(e)}")
    finally:
        cursor.close()
        conn.close()

    return {"resources": resources}