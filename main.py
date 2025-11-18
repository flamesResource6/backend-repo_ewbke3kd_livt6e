import os
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from urllib.parse import urlencode

from database import db, create_document, get_documents

app = FastAPI(title="Editorial + Shopping API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Editorial + Shopping API running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = getattr(db, 'name', None) or "unknown"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response

# -------------------- Models for requests --------------------
class ProductIn(BaseModel):
    title: str
    summary: Optional[str] = None
    description: Optional[str] = None
    brand: Optional[str] = None
    room: Optional[str] = None
    style: Optional[str] = None
    materials: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    rating: Optional[float] = None
    image: Optional[str] = None
    links: Optional[List[Dict[str, Any]]] = None

class ArticleIn(BaseModel):
    title: str
    slug: str
    hero_image: Optional[str] = None
    excerpt: Optional[str] = None
    content: Optional[str] = None
    room: Optional[str] = None
    style: Optional[str] = None
    budget: Optional[str] = None
    tags: Optional[List[str]] = None

class SubscriberIn(BaseModel):
    email: str
    interests: Optional[List[str]] = None
    source: Optional[str] = None

# -------------------- Minimal API routes --------------------
@app.post("/api/products")
def create_product(product: ProductIn):
    try:
        product_id = create_document("product", product.model_dump())
        return {"id": product_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/products")
def list_products(room: Optional[str] = None, style: Optional[str] = None, tag: Optional[str] = None, limit: int = 24):
    try:
        flt: Dict[str, Any] = {}
        if room:
            flt["room"] = room
        if style:
            flt["style"] = style
        if tag:
            flt["tags"] = tag
        docs = get_documents("product", flt, limit)
        # Convert ObjectId to string if present
        for d in docs:
            if "_id" in d:
                d["_id"] = str(d["_id"])
        return {"items": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/articles")
def list_articles(room: Optional[str] = None, style: Optional[str] = None, limit: int = 12):
    try:
        flt: Dict[str, Any] = {}
        if room:
            flt["room"] = room
        if style:
            flt["style"] = style
        docs = get_documents("article", flt, limit)
        for d in docs:
            if "_id" in d:
                d["_id"] = str(d["_id"])
        return {"items": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/subscribe")
def subscribe(sub: SubscriberIn):
    try:
        sub_id = create_document("subscriber", sub.model_dump())
        return {"status": "ok", "id": sub_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/r/{slug}")
def redirect_link(slug: str, request: Request):
    # Link manager: record click and build tracked URL
    doc_list = get_documents("link", {"slug": slug}, limit=1)
    if not doc_list:
        raise HTTPException(status_code=404, detail="Link not found")
    link = doc_list[0]
    # record click
    try:
        headers = request.headers
        click_data = {
            "link_slug": slug,
            "referrer": headers.get("referer"),
            "user_agent": headers.get("user-agent"),
            "ip": request.client.host if request.client else None,
        }
        create_document("click", click_data)
    except Exception:
        pass

    target = link.get("target")
    if not target:
        raise HTTPException(status_code=400, detail="Link target missing")

    # preserve UTM if provided, otherwise append defaults from link doc
    from urllib.parse import urlparse, parse_qs, urlunparse
    parsed = urlparse(target)
    q = parse_qs(parsed.query)
    # add defaults if not present
    for key in ["utm_source", "utm_medium", "utm_campaign"]:
        if key not in q and link.get(key):
            q[key] = [link.get(key)]
    # reconstruct query
    query = urlencode({k: v[0] if isinstance(v, list) else v for k, v in q.items()})
    new_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, query, parsed.fragment))
    return {"redirect": new_url}
