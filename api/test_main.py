import pytest
from fastapi.testclient import TestClient
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
import os
import uuid

# Set environment variables for testing
os.environ["QDRANT_HOST"] = "localhost"
os.environ["QDRANT_PORT"] = "6333"

from main import app, COLLECTION_NAME, VECTOR_SIZE

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_qdrant():
    """Setup Qdrant client and ensure test collection exists"""
    qdrant_client = QdrantClient(host="localhost", port=6333)
    
    # Create collection if it doesn't exist
    try:
        collections = qdrant_client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if COLLECTION_NAME not in collection_names:
            qdrant_client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
            )
    except Exception as e:
        pytest.skip(f"Qdrant is not available: {e}")
    
    yield qdrant_client
    
    # Cleanup after tests (optional)
    # qdrant_client.delete_collection(collection_name=COLLECTION_NAME)

class TestHealthEndpoints:
    """Test health and status endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint returns correct message"""
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()
        assert "running" in response.json()["message"].lower()
    
    def test_health_endpoint(self, setup_qdrant):
        """Test health endpoint returns healthy status"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["qdrant"] == "connected"
        assert "collections" in data
        assert isinstance(data["collections"], int)

class TestDocumentEndpoints:
    """Test document CRUD operations"""
    
    @pytest.fixture
    def sample_document(self):
        """Create a sample document for testing"""
        return {
            "text": "This is a test document for CI/CD pipeline",
            "metadata": {"category": "test", "environment": "ci"}
        }
    
    def test_add_document(self, setup_qdrant, sample_document):
        """Test adding a document"""
        response = client.post("/documents", json=sample_document)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["text"] == sample_document["text"]
        assert data["status"] == "added"
        
        # Store ID for cleanup
        return data["id"]
    
    def test_add_document_with_metadata(self, setup_qdrant):
        """Test adding a document with metadata"""
        doc = {
            "text": "Document with metadata",
            "metadata": {
                "author": "Test User",
                "tags": ["test", "ci/cd"],
                "version": 1
            }
        }
        response = client.post("/documents", json=doc)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["status"] == "added"
    
    def test_get_all_documents(self, setup_qdrant):
        """Test retrieving all documents"""
        response = client.get("/documents")
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert isinstance(data["documents"], list)
        assert "total" in data
        assert "offset" in data
    
    def test_get_documents_with_pagination(self, setup_qdrant):
        """Test document retrieval with pagination"""
        response = client.get("/documents?limit=5&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data["documents"]) <= 5
        assert data["offset"] == 0
    
    def test_delete_document(self, setup_qdrant, sample_document):
        """Test deleting a document"""
        # First, add a document
        add_response = client.post("/documents", json=sample_document)
        doc_id = add_response.json()["id"]
        
        # Then delete it
        delete_response = client.delete(f"/documents/{doc_id}")
        assert delete_response.status_code == 200
        data = delete_response.json()
        assert data["id"] == doc_id
        assert data["status"] == "deleted"

class TestSearchEndpoints:
    """Test search functionality"""
    
    @pytest.fixture
    def seed_documents(self, setup_qdrant):
        """Seed database with test documents for search"""
        documents = [
            {"text": "Machine learning is a subset of artificial intelligence", "metadata": {"topic": "AI"}},
            {"text": "Python is a popular programming language for data science", "metadata": {"topic": "Programming"}},
            {"text": "Vector databases are used for similarity search", "metadata": {"topic": "Database"}},
            {"text": "FastAPI is a modern web framework for building APIs", "metadata": {"topic": "Web"}}
        ]
        
        doc_ids = []
        for doc in documents:
            response = client.post("/documents", json=doc)
            if response.status_code == 200:
                doc_ids.append(response.json()["id"])
        
        yield doc_ids
        
        # Cleanup
        for doc_id in doc_ids:
            client.delete(f"/documents/{doc_id}")
    
    def test_basic_search(self, setup_qdrant, seed_documents):
        """Test basic semantic search"""
        search_query = {
            "query": "What is machine learning?",
            "limit": 5
        }
        response = client.post("/search", json=search_query)
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "results" in data
        assert isinstance(data["results"], list)
        assert len(data["results"]) <= 5
    
    def test_search_with_limit(self, setup_qdrant, seed_documents):
        """Test search with custom limit"""
        search_query = {
            "query": "programming languages",
            "limit": 2
        }
        response = client.post("/search", json=search_query)
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) <= 2
    
    def test_search_results_structure(self, setup_qdrant, seed_documents):
        """Test search results have correct structure"""
        search_query = {
            "query": "databases",
            "limit": 3
        }
        response = client.post("/search", json=search_query)
        assert response.status_code == 200
        data = response.json()
        
        if len(data["results"]) > 0:
            result = data["results"][0]
            assert "id" in result
            assert "score" in result
            assert "text" in result
            assert "metadata" in result
            assert isinstance(result["score"], float)
            assert 0 <= result["score"] <= 1

class TestCollectionEndpoints:
    """Test collection management"""
    
    def test_get_collections(self, setup_qdrant):
        """Test retrieving all collections"""
        response = client.get("/collections")
        assert response.status_code == 200
        data = response.json()
        assert "collections" in data
        assert isinstance(data["collections"], list)
    
    def test_create_collection(self, setup_qdrant):
        """Test creating a new collection"""
        test_collection_name = f"test_collection_{uuid.uuid4().hex[:8]}"
        collection_data = {
            "name": test_collection_name,
            "vector_size": 384,
            "distance": "Cosine"
        }
        response = client.post("/collections", json=collection_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == test_collection_name
        assert data["status"] == "created"
        
        # Cleanup: Delete the test collection
        client.delete(f"/collections/{test_collection_name}")
    
    def test_create_duplicate_collection(self, setup_qdrant):
        """Test creating a duplicate collection returns error"""
        test_collection_name = f"test_dup_collection_{uuid.uuid4().hex[:8]}"
        collection_data = {
            "name": test_collection_name,
            "vector_size": 384,
            "distance": "Cosine"
        }
        
        # Create first time
        response1 = client.post("/collections", json=collection_data)
        assert response1.status_code == 200
        
        # Try to create again
        response2 = client.post("/collections", json=collection_data)
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"].lower()
        
        # Cleanup
        client.delete(f"/collections/{test_collection_name}")
    
    def test_get_collection_info(self, setup_qdrant):
        """Test getting collection information"""
        response = client.get(f"/collections/{COLLECTION_NAME}/info")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "vectors_count" in data
        assert "points_count" in data
        assert "status" in data
        assert data["name"] == COLLECTION_NAME
    
    def test_delete_collection(self, setup_qdrant):
        """Test deleting a collection"""
        # Create a test collection first
        test_collection_name = f"test_delete_collection_{uuid.uuid4().hex[:8]}"
        collection_data = {
            "name": test_collection_name,
            "vector_size": 384,
            "distance": "Cosine"
        }
        create_response = client.post("/collections", json=collection_data)
        assert create_response.status_code == 200
        
        # Now delete it
        delete_response = client.delete(f"/collections/{test_collection_name}")
        assert delete_response.status_code == 200
        data = delete_response.json()
        assert data["name"] == test_collection_name
        assert data["status"] == "deleted"

class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_delete_nonexistent_document(self, setup_qdrant):
        """Test deleting a non-existent document"""
        fake_id = str(uuid.uuid4())
        response = client.delete(f"/documents/{fake_id}")
        # Should either return 200 (Qdrant doesn't error) or 500
        assert response.status_code in [200, 500]
    
    def test_get_nonexistent_collection_info(self, setup_qdrant):
        """Test getting info for non-existent collection"""
        response = client.get("/collections/nonexistent_collection/info")
        assert response.status_code == 500
    
    def test_search_with_invalid_data(self, setup_qdrant):
        """Test search with invalid query structure"""
        response = client.post("/search", json={"invalid": "data"})
        assert response.status_code == 422  # Validation error

class TestIntegration:
    """Integration tests for complete workflows"""
    
    def test_complete_document_lifecycle(self, setup_qdrant):
        """Test complete document lifecycle: add, search, retrieve, delete"""
        # 1. Add document
        doc = {
            "text": "Integration test document for complete lifecycle",
            "metadata": {"test": "integration", "lifecycle": True}
        }
        add_response = client.post("/documents", json=doc)
        assert add_response.status_code == 200
        doc_id = add_response.json()["id"]
        
        # 2. Search for document
        search_response = client.post("/search", json={"query": "integration test", "limit": 10})
        assert search_response.status_code == 200
        results = search_response.json()["results"]
        assert any(r["id"] == doc_id for r in results)
        
        # 3. Retrieve all documents
        get_response = client.get("/documents")
        assert get_response.status_code == 200
        documents = get_response.json()["documents"]
        assert any(d["id"] == doc_id for d in documents)
        
        # 4. Delete document
        delete_response = client.delete(f"/documents/{doc_id}")
        assert delete_response.status_code == 200
        assert delete_response.json()["status"] == "deleted"
    
    def test_collection_and_document_workflow(self, setup_qdrant):
        """Test creating a collection and adding documents to it"""
        # Note: This test uses the default collection since the current API
        # doesn't support specifying collection per document operation
        
        # Get initial collection count
        collections_response = client.get("/collections")
        assert collections_response.status_code == 200
        initial_count = len(collections_response.json()["collections"])
        
        # Create new collection
        test_collection = f"workflow_test_{uuid.uuid4().hex[:8]}"
        create_response = client.post("/collections", json={
            "name": test_collection,
            "vector_size": 384,
            "distance": "Cosine"
        })
        assert create_response.status_code == 200
        
        # Verify collection count increased
        collections_response = client.get("/collections")
        assert len(collections_response.json()["collections"]) == initial_count + 1
        
        # Get collection info
        info_response = client.get(f"/collections/{test_collection}/info")
        assert info_response.status_code == 200
        
        # Cleanup
        delete_response = client.delete(f"/collections/{test_collection}")
        assert delete_response.status_code == 200

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
