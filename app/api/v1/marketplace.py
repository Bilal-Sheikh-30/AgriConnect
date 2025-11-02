from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from app.db.database import get_db_connection
from app.utils.jwt_util import get_current_user
import cloudinary.uploader
import os
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

router = APIRouter(prefix="/marketplace", tags=["marketplace"])

# get all available items
@router.get("/available")
def get_available_items():
    """
    Get all items where status = 'available',
    including seller's name, province, and city
    """
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute('''
            SELECT i.id, i.name, i.category, i.image, i.price, i.quantity, i.status,
                   i.seller, u.name AS seller_name, u.province AS seller_province, u.city AS seller_city
            FROM item i
            JOIN "user" u ON i.seller = u.id
            WHERE i.status = %s;
        ''', ("available",))

        items = cursor.fetchall()

        for item in items:
            if item["price"] is not None:
                item["price"] = float(item["price"])

        cursor.close()
        conn.close()

        if not items:
            return {"message": "No available items found.", "items": []}

        return {"items": items}

    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create")
async def create_item(
    name: str = Form(...),
    category: str = Form(...),
    price: float = Form(...),
    quantity: str = Form(...),  
    image: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cursor = conn.cursor()

    # Upload image to Cloudinary
    try:
        upload_result = cloudinary.uploader.upload(image.file, folder="items")
        image_url = upload_result.get("secure_url")
    except Exception as e:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")

    try:
        cursor.execute(
            """
            INSERT INTO item (name, category, image, price, quantity, status, seller)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id, name, category, image, price, quantity, status, seller;
            """,
            (name, category, image_url, price, quantity, "available", current_user["id"])
        )
        new_item = cursor.fetchone()
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"DB insert failed: {str(e)}")
    finally:
        cursor.close()
        conn.close()

    if new_item and new_item["price"] is not None:
        new_item["price"] = float(new_item["price"])

    return {"message": "Item created successfully!", "item": new_item}



@router.get("/my-items")
async def get_my_items(current_user: dict = Depends(get_current_user)):
    """
    Get all items belonging to the logged-in user
    """
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute(
            """
            SELECT id, name, category, image, price, quantity, status, seller
            FROM item
            WHERE seller = %s
            """,
            (current_user["id"],)
        )
        items = cursor.fetchall()

        for item in items:
            if item["price"] is not None:
                item["price"] = float(item["price"])

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch items: {str(e)}")
    finally:
        cursor.close()
        conn.close()

    return {"items": items}
