import os
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from urllib.parse import urlencode

from database import db, create_document, get_documents

# bson for ObjectId handling
try:
    from bson import ObjectId
except Exception:
    ObjectId = None

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
    inline_products: Optional[List[Dict[str, Any]]] = None

class SubscriberIn(BaseModel):
    email: str
    interests: Optional[List[str]] = None
    source: Optional[str] = None

class LinkIn(BaseModel):
    slug: str
    target: str
    utm_campaign: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    source: Optional[str] = None

class CollectionIn(BaseModel):
    title: str
    slug: str
    description: Optional[str] = None
    cover_image: Optional[str] = None
    product_ids: Optional[List[str]] = None
    tags: Optional[List[str]] = None

class WishlistIn(BaseModel):
    user_id: str
    product_id: str
    notes: Optional[str] = None

# -------------------- Utilities --------------------
def _safe_id(doc: Dict[str, Any]) -> Dict[str, Any]:
    if not doc:
        return doc
    d = dict(doc)
    if "_id" in d:
        d["_id"] = str(d["_id"])
    return d

# -------------------- Products --------------------
@app.post("/api/products")
def create_product(product: ProductIn):
    try:
        product_id = create_document("product", product.model_dump())
        return {"id": product_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/products")
def list_products(room: Optional[str] = None, style: Optional[str] = None, tag: Optional[str] = None, q: Optional[str] = None, limit: int = 24):
    try:
        flt: Dict[str, Any] = {}
        if room:
            flt["room"] = room
        if style:
            flt["style"] = style
        if tag:
            flt["tags"] = tag
        if q:
            flt["$or"] = [
                {"title": {"$regex": q, "$options": "i"}},
                {"summary": {"$regex": q, "$options": "i"}},
                {"brand": {"$regex": q, "$options": "i"}},
                {"tags": {"$regex": q, "$options": "i"}},
            ]
        docs = get_documents("product", flt, limit)
        return {"items": [_safe_id(d) for d in docs]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/products/{product_id}")
def get_product(product_id: str):
    try:
        if ObjectId is None:
            raise HTTPException(status_code=500, detail="ObjectId not available")
        doc = db["product"].find_one({"_id": ObjectId(product_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Product not found")
        return _safe_id(doc)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------- Articles --------------------
@app.post("/api/articles")
def create_article(article: ArticleIn):
    try:
        article_id = create_document("article", article.model_dump())
        return {"id": article_id}
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
        return {"items": [_safe_id(d) for d in docs]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/articles/{slug}")
def get_article(slug: str):
    try:
        doc = db["article"].find_one({"slug": slug})
        if not doc:
            raise HTTPException(status_code=404, detail="Article not found")
        return _safe_id(doc)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------- Collections --------------------
@app.post("/api/collections")
def create_collection(col: CollectionIn):
    try:
        col_id = create_document("collection", col.model_dump())
        return {"id": col_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/collections")
def list_collections(tag: Optional[str] = None, limit: int = 20):
    try:
        flt: Dict[str, Any] = {}
        if tag:
            flt["tags"] = tag
        docs = get_documents("collection", flt, limit)
        return {"items": [_safe_id(d) for d in docs]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------- Links --------------------
@app.post("/api/links")
def create_link(link: LinkIn):
    try:
        # ensure slug unique
        existing = db["link"].find_one({"slug": link.slug})
        if existing:
            raise HTTPException(status_code=400, detail="Slug already exists")
        link_id = create_document("link", link.model_dump())
        return {"id": link_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/links/{slug}")
def get_link(slug: str):
    try:
        doc = db["link"].find_one({"slug": slug})
        if not doc:
            raise HTTPException(status_code=404, detail="Link not found")
        return _safe_id(doc)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------- Subscribe --------------------
@app.post("/api/subscribe")
def subscribe(sub: SubscriberIn):
    try:
        sub_id = create_document("subscriber", sub.model_dump())
        return {"status": "ok", "id": sub_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------- Wishlist --------------------
@app.post("/api/wishlist")
def add_wishlist(item: WishlistIn):
    try:
        wid = create_document("wishlistitem", item.model_dump())
        return {"id": wid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/wishlist")
def get_wishlist(user_id: str, limit: int = 200):
    try:
        docs = get_documents("wishlistitem", {"user_id": user_id}, limit)
        return {"items": [_safe_id(d) for d in docs]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/wishlist/{item_id}")
def delete_wishlist_item(item_id: str):
    try:
        if ObjectId is None:
            raise HTTPException(status_code=500, detail="ObjectId not available")
        res = db["wishlistitem"].delete_one({"_id": ObjectId(item_id)})
        if res.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Item not found")
        return {"status": "deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------- Search --------------------
@app.get("/api/search")
def search(q: str, limit: int = 10):
    try:
        regex = {"$regex": q, "$options": "i"}
        products = list(db["product"].find({"$or": [{"title": regex}, {"summary": regex}, {"brand": regex}, {"tags": regex}]}).limit(limit))
        articles = list(db["article"].find({"$or": [{"title": regex}, {"excerpt": regex}, {"tags": regex}]}).limit(limit))
        return {
            "products": [_safe_id(d) for d in products],
            "articles": [_safe_id(d) for d in articles]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------- Analytics --------------------
@app.get("/api/analytics/summary")
def analytics_summary():
    try:
        def count(col: str) -> int:
            return db[col].count_documents({}) if db is not None else 0
        return {
            "products": count("product"),
            "articles": count("article"),
            "collections": count("collection"),
            "links": count("link"),
            "clicks": count("click"),
            "subscribers": count("subscriber")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------- Redirect Manager --------------------
@app.get("/r/{slug}")
def redirect_link(slug: str, request: Request):
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

    from urllib.parse import urlparse, parse_qs, urlunparse
    parsed = urlparse(target)
    q = parse_qs(parsed.query)
    # add defaults if not present
    for key in ["utm_source", "utm_medium", "utm_campaign"]:
        if key not in q and link.get(key):
            q[key] = [link.get(key)]
    query = urlencode({k: v[0] if isinstance(v, list) else v for k, v in q.items()})
    new_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, query, parsed.fragment))
    # issue an HTTP redirect so clicks flow through naturally
    return RedirectResponse(url=new_url, status_code=307)
