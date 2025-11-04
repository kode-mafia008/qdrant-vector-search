from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import os
import uuid
from typing import List, Optional

app = FastAPI(title="Qdrant Vector DB API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Qdrant client
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

# Initialize embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")
VECTOR_SIZE = 384

# Default collection name
COLLECTION_NAME = "documents"


class Document(BaseModel):
    text: str
    metadata: Optional[dict] = {}


class SearchQuery(BaseModel):
    query: str
    limit: int = 5


class CollectionCreate(BaseModel):
    name: str
    vector_size: Optional[int] = 384
    distance: Optional[str] = "Cosine"


@app.on_event("startup")
async def startup_event():
    """Create collection on startup if it doesn't exist"""
    collections = client.get_collections().collections
    collection_names = [c.name for c in collections]

    if COLLECTION_NAME not in collection_names:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
        print(f"Created collection: {COLLECTION_NAME}")


@app.get("/")
async def root():
    return {"message": "Qdrant Vector DB API is running!"}


@app.get("/health")
async def health():
    try:
        collections = client.get_collections()
        return {
            "status": "healthy",
            "qdrant": "connected",
            "collections": len(collections.collections),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/documents")
async def add_document(doc: Document):
    """Add a document with automatic embedding"""
    try:
        # Generate embedding
        vector = model.encode(doc.text).tolist()

        # Generate unique ID
        doc_id = str(uuid.uuid4())

        # Create point
        point = PointStruct(
            id=doc_id, vector=vector, payload={"text": doc.text, **doc.metadata}
        )

        # Upload to Qdrant
        client.upsert(collection_name=COLLECTION_NAME, points=[point])

        return {"id": doc_id, "text": doc.text, "status": "added"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search")
async def search_documents(query: SearchQuery):
    """Search for similar documents"""
    try:
        # Generate query embedding
        query_vector = model.encode(query.query).tolist()

        # Search
        results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=query.limit,
        )

        return {
            "query": query.query,
            "results": [
                {
                    "id": str(hit.id),
                    "score": hit.score,
                    "text": hit.payload.get("text", ""),
                    "metadata": {k: v for k, v in hit.payload.items() if k != "text"},
                }
                for hit in results
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents")
async def get_all_documents(limit: int = 100, offset: int = 0):
    """Get all documents"""
    try:
        result = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=limit,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )

        points, next_offset = result

        return {
            "documents": [
                {
                    "id": str(point.id),
                    "text": point.payload.get("text", ""),
                    "metadata": {k: v for k, v in point.payload.items() if k != "text"},
                }
                for point in points
            ],
            "total": len(points),
            "offset": offset,
            "next_offset": next_offset,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document by ID"""
    try:
        client.delete(collection_name=COLLECTION_NAME, points_selector=[doc_id])
        return {"id": doc_id, "status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/collections")
async def get_collections():
    """Get all collections"""
    try:
        collections = client.get_collections().collections
        return {
            "collections": [
                {
                    "name": c.name,
                }
                for c in collections
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/collections")
async def create_collection(collection: CollectionCreate):
    """Create a new collection"""
    try:
        # Check if collection already exists
        collections = client.get_collections().collections
        collection_names = [c.name for c in collections]

        if collection.name in collection_names:
            raise HTTPException(
                status_code=400, detail=f"Collection '{collection.name}' already exists"
            )

        # Map distance string to Distance enum
        distance_map = {
            "Cosine": Distance.COSINE,
            "Euclid": Distance.EUCLID,
            "Dot": Distance.DOT,
        }

        distance_metric = distance_map.get(collection.distance, Distance.COSINE)

        # Create collection
        client.create_collection(
            collection_name=collection.name,
            vectors_config=VectorParams(
                size=collection.vector_size, distance=distance_metric
            ),
        )

        return {
            "name": collection.name,
            "vector_size": collection.vector_size,
            "distance": collection.distance,
            "status": "created",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/collections/{collection_name}/info")
async def get_collection_info(collection_name: str):
    """Get collection information"""
    try:
        info = client.get_collection(collection_name=collection_name)
        return {
            "name": collection_name,
            "vectors_count": info.vectors_count,
            "points_count": info.points_count,
            "status": info.status,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/collections/{collection_name}")
async def delete_collection(collection_name: str):
    """Delete a collection"""
    try:
        client.delete_collection(collection_name=collection_name)
        return {"name": collection_name, "status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
