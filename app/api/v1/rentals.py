from fastapi import APIRouter, HTTPException, Depends
from uuid import UUID
from datetime import datetime, timezone
from app.db.database import get_db_connection
from app.utils.jwt_util import get_current_user
import psycopg2.extras

router = APIRouter()


@router.post("/equipment/{equipment_id}/rent", status_code=201)
def rent_equipment(equipment_id: UUID, payload: dict, current_user: dict = Depends(get_current_user)):
    """
    Endpoint to rent equipment. Expects JSON body with start_time, end_time, duration_hours, total_price, note.
    """
    # basic validation of payload fields
    if not payload.get("start_time") or not payload.get("end_time"):
        raise HTTPException(status_code=400, detail="start_time and end_time are required")

    # parse ISO datetimes (support trailing Z)
    def parse_iso(s: str) -> datetime:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(s)
        except Exception:
            raise HTTPException(status_code=400, detail=f"Invalid ISO datetime: {s}")
        # ensure timezone-aware
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    start = parse_iso(payload["start_time"])
    end = parse_iso(payload["end_time"])

    if start >= end:
        raise HTTPException(status_code=400, detail="Invalid times: start_time must be before end_time")

    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor()

        # 1) Lock resource row for update to avoid race conditions
        # use RealDictCursor semantics (rows are dict-like)
        cursor.execute('SELECT id, owner, rent_per_hour FROM "Resource" WHERE id = %s FOR UPDATE;', (str(equipment_id),))
        resource = cursor.fetchone()
        if not resource:
            conn.rollback()
            raise HTTPException(status_code=404, detail="Resource not found")

        resource_owner = resource.get("owner")
        # price column in DB is `rent_per_hour`
        price_per_hour = resource.get("rent_per_hour")
        if price_per_hour is None:
            conn.rollback()
            raise HTTPException(status_code=500, detail="Resource price not set")

        # 2) Owners cannot rent their own resource
        if str(resource_owner) == str(current_user["id"]):
            conn.rollback()
            raise HTTPException(status_code=403, detail="Owners cannot rent their own resource")

        # 3) compute duration and price server-side
        duration_hours = (end - start).total_seconds() / 3600
        # allow fractional hours
        total_price_server = float(price_per_hour) * duration_hours

        # 4) check for overlapping rentals
        # We treat bookings as half-open intervals [start, end): conflict if existing.rented_to > start AND existing.rented_from < end
        # Note: the DB uses column names with spaces: "rented from", "rented to"
        cursor.execute(
            'SELECT id, "rented from", "rented to" FROM "Rentals" WHERE resource = %s AND "rented to" > %s AND "rented from" < %s LIMIT 1;',
            (str(equipment_id), start, end)
        )
        conflict = cursor.fetchone()
        if conflict:
            conn.rollback()
            # format dates for message
            existing_from = conflict.get("rented from")
            existing_to = conflict.get("rented to")
            raise HTTPException(status_code=409, detail=f"Resource already booked between {existing_from} and {existing_to}")

        # 5) create rental
        cursor.execute(
            'INSERT INTO "Rentals" (owner, renter, resource, "rented from", "rented to") VALUES (%s, %s, %s, %s, %s) RETURNING id, owner, renter, resource, "rented from", "rented to";',
            (str(resource_owner), str(current_user["id"]), str(equipment_id), start, end)
        )
        new_rental = cursor.fetchone()

        # mark resource as unavailable for the booked period
        # Note: this sets a single status flag. To make availability time-aware,
        # consider computing availability from Rentals rows or adding an availability calendar.
        cursor.execute('UPDATE "Resource" SET status = %s WHERE id = %s;', ("unavailable", str(equipment_id)))

        conn.commit()

        rental_id = new_rental.get("id")
        owner_id = new_rental.get("owner")
        renter_id = new_rental.get("renter")
        resource_id = new_rental.get("resource")
        rented_from = new_rental.get("rented from")
        rented_to = new_rental.get("rented to")

        return {
            "rental_id": rental_id,
            "owner": owner_id,
            "renter": renter_id,
            "resource": resource_id,
            "start_time": rented_from.isoformat() if hasattr(rented_from, 'isoformat') else rented_from,
            "end_time": rented_to.isoformat() if hasattr(rented_to, 'isoformat') else rented_to,
            "duration_hours": duration_hours,
            "total_price": total_price_server,
        }

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass



@router.get("/my-borrowed")
async def get_my_borrowed(current_user: dict = Depends(get_current_user)):
    """
    Get all rentals where the logged-in user is the renter,
    including owner details, ordered by most recent rental first.
    """
    print(f'\ncurrent user: {current_user["id"]}')
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Join Rentals with Resource and User (owner) to get all info
        cursor.execute('''
    SELECT 
        r.id AS rental_id,
        res.id AS resource_id,
        res.title AS resource_title,
        res.category AS resource_category,
        res.image AS resource_image,
        res."rent_per_hour" AS rent_per_hour,
        r."rented from" AS rented_from,
        r."rented to" AS rented_to,
        u.id AS owner_id,
        u.name AS owner_name,
        u.province AS owner_province,
        u.city AS owner_city
    FROM "Rentals" r
    JOIN "Resource" res ON r.resource = res.id
    JOIN "user" u ON r.owner = u.id
    WHERE r.renter = %s
    ORDER BY r."rented from" DESC
''', (current_user["id"],))


        borrowed_items = cursor.fetchall()

        # Convert Decimal to float for rent_per_hour
        for item in borrowed_items:
            if item["rent_per_hour"] is not None:
                item["rent_per_hour"] = float(item["rent_per_hour"])

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch borrowed items: {str(e)}")
    finally:
        cursor.close()
        conn.close()

    return {"borrowed_items": borrowed_items}