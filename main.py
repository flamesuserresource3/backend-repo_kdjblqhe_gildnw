import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Dict, Any, List, Optional
from datetime import datetime

from schemas import ALL_SCHEMAS, Master, Client, Booking
from database import create_document, get_documents

app = FastAPI(title="BeautyConnect API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "BeautyConnect backend is running"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/schema")
def get_schema():
    """Expose declared Pydantic models so DB viewer can use them."""
    out: Dict[str, Dict[str, Any]] = {}
    for name, model in ALL_SCHEMAS.items():
        out[name] = model.model_json_schema()
    return out

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        from database import db
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = getattr(db, 'name', None) or os.getenv("DATABASE_NAME") or "Unknown"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response

# ---------------------
# Masters API
# ---------------------

class MasterOut(BaseModel):
    id: str
    name: str
    role: Optional[str] = None
    rating: float = 0
    reviews_count: int = 0
    city: Optional[str] = None
    avatar: Optional[str] = None
    verified: bool = False


def _serialize_master(doc: dict) -> MasterOut:
    return MasterOut(
        id=str(doc.get("_id")),
        name=doc.get("name", ""),
        role=(doc.get("skills") or [None])[0],
        rating=float(doc.get("rating", 0)),
        reviews_count=int(doc.get("reviews_count", 0)),
        city=doc.get("city"),
        avatar=doc.get("avatar"),
        verified=bool(doc.get("verified", False)),
    )

@app.get("/api/masters", response_model=List[MasterOut])
def list_masters(city: Optional[str] = Query(default=None, description="Filter by city"), limit: int = Query(default=12, ge=1, le=100)):
    filter_q = {}
    if city:
        filter_q["city"] = city
    try:
        docs = get_documents("master", filter_q, limit=limit)
        return [_serialize_master(d) for d in docs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/masters", status_code=201)
def create_master(master: Master):
    try:
        new_id = create_document("master", master)
        return {"id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Simple seed endpoint for demo purposes
@app.post("/api/seed", tags=["dev"])
def seed_demo_data():
    sample = [
        Master(name="Анна Петрова", city="Москва", skills=["Визажист"], rating=4.9, reviews_count=182, avatar="https://images.unsplash.com/photo-1527980965255-d3b416303d12?q=80&w=300&auto=format&fit=crop"),
        Master(name="Ирина Смирнова", city="Санкт-Петербург", skills=["Мастер маникюра"], rating=4.8, reviews_count=240, avatar="https://images.unsplash.com/photo-1544005313-94ddf0286df2?q=80&w=300&auto=format&fit=crop"),
        Master(name="Мария Иванова", city="Казань", skills=["Парикмахер-стилист"], rating=5.0, reviews_count=320, avatar="https://images.unsplash.com/photo-1502685104226-ee32379fefbe?q=80&w=300&auto=format&fit=crop"),
    ]
    try:
        ids = [create_document("master", m) for m in sample]
        return {"inserted": len(ids), "ids": ids}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------
# Booking API
# ---------------------

class BookingRequest(BaseModel):
    master_id: str
    name: str
    email: EmailStr
    datetime_utc: datetime
    notes: Optional[str] = None

class BookingOut(BaseModel):
    id: str
    status: str

@app.post("/api/bookings", response_model=BookingOut, status_code=201)
def create_booking(req: BookingRequest):
    try:
        # Create client first
        client = Client(name=req.name, email=req.email)
        client_id = create_document("client", client)
        # Create booking (service unknown at this stage)
        booking = Booking(
            master_id=req.master_id,
            client_id=client_id,
            service_id="unknown",
            datetime_utc=req.datetime_utc,
            status="pending",
            notes=req.notes,
        )
        booking_id = create_document("booking", booking)
        return BookingOut(id=booking_id, status="pending")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bookings")
def list_bookings(master_id: Optional[str] = None, limit: int = Query(default=50, ge=1, le=200)):
    try:
        q = {"master_id": master_id} if master_id else {}
        docs = get_documents("booking", q, limit=limit)
        # sanitize ids
        for d in docs:
            d["id"] = str(d.pop("_id", ""))
        return docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
