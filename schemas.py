"""
Database Schemas for BeautyConnect

Each Pydantic model represents a MongoDB collection.
Collection name is the lowercase of the class name (e.g., Master -> "master").
"""
from pydantic import BaseModel, Field, EmailStr, HttpUrl
from typing import Optional, List, Literal
from datetime import datetime

# Core entities

class Master(BaseModel):
    name: str = Field(..., description="Full name of the beauty professional")
    email: Optional[EmailStr] = Field(None, description="Contact email")
    phone: Optional[str] = Field(None, description="Contact phone number")
    city: Optional[str] = Field(None, description="City / location")
    bio: Optional[str] = Field(None, description="Short bio/description")
    avatar: Optional[HttpUrl] = Field(None, description="Profile image URL")
    skills: List[str] = Field(default_factory=list, description="List of skills/tags")
    rating: float = Field(0, ge=0, le=5, description="Average rating")
    reviews_count: int = Field(0, ge=0, description="Number of reviews")

class Client(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    avatar: Optional[HttpUrl] = None

class Service(BaseModel):
    title: str
    category: str = Field(..., description="Top-level category")
    subcategory: Optional[str] = Field(None, description="Subcategory")
    description: Optional[str] = None
    price: float = Field(..., ge=0)
    duration_min: int = Field(..., ge=10, le=480, description="Duration in minutes")
    master_id: Optional[str] = Field(None, description="ID of master providing the service")

class Booking(BaseModel):
    master_id: str
    client_id: str
    service_id: str
    datetime_utc: datetime
    status: Literal['pending', 'confirmed', 'completed', 'cancelled'] = 'pending'
    notes: Optional[str] = None

class Review(BaseModel):
    master_id: str
    client_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

class Portfolioitem(BaseModel):
    master_id: str
    title: Optional[str] = None
    image_url: HttpUrl
    tags: List[str] = Field(default_factory=list)

# Minimal map for schema endpoint (used by Flames DB viewer)
ALL_SCHEMAS = {
    'master': Master,
    'client': Client,
    'service': Service,
    'booking': Booking,
    'review': Review,
    'portfolioitem': Portfolioitem,
}
