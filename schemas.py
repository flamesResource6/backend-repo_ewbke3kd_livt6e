"""
Database Schemas for Editorial + Shopping Site

Each Pydantic model maps to a MongoDB collection using the lowercase of the class name.
Examples:
- Article -> "article"
- Product -> "product"
- Collection -> "collection"
- Link -> "link"
- Wishlist -> "wishlist"
- Subscriber -> "subscriber"

These schemas are used for validation and by the database viewer.
"""
from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl

class ProductAffiliateLink(BaseModel):
    retailer: str = Field(..., description="Retailer name, e.g., Amazon, Wayfair")
    url: HttpUrl = Field(..., description="Affiliate URL with tracking")
    price: Optional[float] = Field(None, ge=0)
    availability: Optional[str] = Field(None, description="In Stock, Backorder, etc.")

class Product(BaseModel):
    title: str
    summary: Optional[str] = None
    description: Optional[str] = None
    brand: Optional[str] = None
    room: Optional[str] = Field(None, description="Living Room, Bedroom, Kitchen, etc.")
    style: Optional[str] = Field(None, description="Modern, Minimal, Boho, etc.")
    materials: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    rating: Optional[float] = Field(None, ge=0, le=5)
    image: Optional[HttpUrl] = None
    links: List[ProductAffiliateLink] = Field(default_factory=list)

class ArticleInlineProduct(BaseModel):
    product_id: Optional[str] = Field(None, description="Reference to product _id as string")
    title: Optional[str] = None
    retailer: Optional[str] = None
    url: Optional[HttpUrl] = None

class Article(BaseModel):
    title: str
    slug: str
    hero_image: Optional[HttpUrl] = None
    excerpt: Optional[str] = None
    content: Optional[str] = Field(None, description="Rich text or markdown")
    room: Optional[str] = None
    style: Optional[str] = None
    budget: Optional[str] = Field(None, description="Under $1000, Luxury, etc.")
    tags: Optional[List[str]] = None
    inline_products: Optional[List[ArticleInlineProduct]] = None

class Collection(BaseModel):
    title: str
    slug: str
    description: Optional[str] = None
    cover_image: Optional[HttpUrl] = None
    product_ids: List[str] = Field(default_factory=list, description="List of product _ids as strings")
    tags: Optional[List[str]] = None

class Link(BaseModel):
    slug: str = Field(..., description="Short code used in redirect URL, e.g., /r/sofa123")
    target: HttpUrl = Field(..., description="Destination affiliate URL")
    source: Optional[str] = Field(None, description="Placement: article slug, component, etc.")
    utm_campaign: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None

class Click(BaseModel):
    link_slug: str
    referrer: Optional[str] = None
    user_agent: Optional[str] = None
    ip: Optional[str] = None

class WishlistItem(BaseModel):
    user_id: Optional[str] = Field(None, description="Anonymous or account user id")
    product_id: str
    notes: Optional[str] = None

class Subscriber(BaseModel):
    email: str
    interests: Optional[List[str]] = None
    source: Optional[str] = None
