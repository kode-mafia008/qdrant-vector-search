# Testing Guide

This document provides comprehensive information about testing the Qdrant Vector Search Platform.

## Table of Contents
- [Quick Start](#quick-start)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [CI/CD Pipeline](#cicd-pipeline)
- [Writing New Tests](#writing-new-tests)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Prerequisites

1. **Qdrant Running**: Ensure Qdrant is running locally
   ```bash
   docker compose up -d qdrant
   ```

2. **Install Dependencies**:
   ```bash
   cd api
   pip install -r requirements.txt
   ```

### Run Tests

```bash
# Run all tests
pytest test_main.py -v

# Run specific test class
pytest test_main.py::TestHealthEndpoints -v

# Run specific test
pytest test_main.py::TestHealthEndpoints::test_health_endpoint -v
```

## Test Structure

The test suite is organized into the following test classes:

### 1. TestHealthEndpoints
Tests for API health and status endpoints.
- `test_root_endpoint()` - Verify root endpoint response
- `test_health_endpoint()` - Check health check functionality

### 2. TestDocumentEndpoints
Tests for document CRUD operations.
- `test_add_document()` - Add document to collection
- `test_add_document_with_metadata()` - Add document with metadata
- `test_get_all_documents()` - Retrieve all documents
- `test_get_documents_with_pagination()` - Test pagination
- `test_delete_document()` - Delete document by ID

### 3. TestSearchEndpoints
Tests for semantic search functionality.
- `test_basic_search()` - Basic semantic search
- `test_search_with_limit()` - Search with custom limit
- `test_search_results_structure()` - Verify result structure

### 4. TestCollectionEndpoints
Tests for collection management.
- `test_get_collections()` - List all collections
- `test_create_collection()` - Create new collection
- `test_create_duplicate_collection()` - Handle duplicates
- `test_get_collection_info()` - Get collection details
- `test_delete_collection()` - Delete collection

### 5. TestErrorHandling
Tests for error scenarios and edge cases.
- `test_delete_nonexistent_document()` - Handle missing documents
- `test_get_nonexistent_collection_info()` - Handle missing collections
- `test_search_with_invalid_data()` - Validate input validation

### 6. TestIntegration
End-to-end integration tests.
- `test_complete_document_lifecycle()` - Full document workflow
- `test_collection_and_document_workflow()` - Collection operations

## Running Tests

### Basic Commands

```bash
# Run all tests with verbose output
pytest test_main.py -v

# Run tests with short traceback
pytest test_main.py --tb=short

# Run tests with colored output
pytest test_main.py --color=yes

# Stop at first failure
pytest test_main.py -x

# Run last failed tests
pytest test_main.py --lf
```

### Test Selection

```bash
# Run specific test class
pytest test_main.py::TestHealthEndpoints

# Run specific test method
pytest test_main.py::TestHealthEndpoints::test_root_endpoint

# Run tests matching pattern
pytest test_main.py -k "health"

# Run tests with marker (if defined)
pytest test_main.py -m integration
```

### Coverage Reports

```bash
# Install pytest-cov
pip install pytest-cov

# Run with coverage
pytest test_main.py --cov=main --cov-report=term-missing

# Generate HTML coverage report
pytest test_main.py --cov=main --cov-report=html

# Open coverage report
open htmlcov/index.html
```

### Output Options

```bash
# Quiet mode (less output)
pytest test_main.py -q

# Show local variables in tracebacks
pytest test_main.py -l

# Show print statements
pytest test_main.py -s

# Generate JUnit XML report
pytest test_main.py --junit-xml=test-results.xml
```

## CI/CD Pipeline

### GitHub Actions Workflow

The CI/CD pipeline is defined in `.github/workflows/test.yml` and includes:

#### Test Job
- Sets up Python 3.11
- Starts Qdrant service container
- Installs dependencies
- Runs pytest with coverage
- Uploads test results as artifacts

#### Lint Job
- Runs flake8 for code quality
- Checks code formatting with black

#### Security Job
- Runs safety check for vulnerable dependencies
- Performs bandit security scan

#### Docker Build Job
- Validates Docker images build successfully
- Tests docker-compose configuration

### Viewing CI/CD Results

1. Go to the GitHub repository
2. Click on the **Actions** tab
3. Select a workflow run to see detailed results
4. Download test artifacts for detailed reports

### CI/CD Badge

Add this badge to your README to show build status:
```markdown
[![CI/CD Tests](https://github.com/kode-mafia008/qdrant-vector-search/actions/workflows/test.yml/badge.svg)](https://github.com/kode-mafia008/qdrant-vector-search/actions/workflows/test.yml)
```

## Writing New Tests

### Test Template

```python
class TestNewFeature:
    """Test description"""
    
    @pytest.fixture
    def setup_data(self):
        """Setup fixture for test data"""
        # Setup code
        data = {"key": "value"}
        yield data
        # Teardown code (optional)
    
    def test_feature_functionality(self, setup_data):
        """Test specific functionality"""
        # Arrange
        test_input = setup_data
        
        # Act
        response = client.post("/endpoint", json=test_input)
        
        # Assert
        assert response.status_code == 200
        assert response.json()["status"] == "success"
```

### Best Practices

1. **Test Naming**: Use descriptive names starting with `test_`
2. **Arrange-Act-Assert**: Structure tests clearly
3. **Fixtures**: Use fixtures for setup/teardown
4. **Independence**: Tests should not depend on each other
5. **Cleanup**: Always clean up test data
6. **Documentation**: Add docstrings to test methods

### Adding Fixtures

```python
@pytest.fixture(scope="module")
def qdrant_client():
    """Create Qdrant client for tests"""
    client = QdrantClient(host="localhost", port=6333)
    yield client
    # Optional cleanup

@pytest.fixture(scope="function")
def sample_document():
    """Create sample document for each test"""
    return {
        "text": "Test document",
        "metadata": {"type": "test"}
    }
```

### Test Markers

Add custom markers in `pytest.ini`:

```ini
[pytest]
markers =
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    slow: marks tests as slow running
```

Use markers in tests:

```python
@pytest.mark.integration
def test_full_workflow():
    """Integration test for complete workflow"""
    pass

@pytest.mark.slow
def test_large_dataset():
    """Test with large dataset"""
    pass
```

Run specific markers:
```bash
pytest -m integration  # Run only integration tests
pytest -m "not slow"   # Skip slow tests
```

## Troubleshooting

### Common Issues

#### 1. Qdrant Connection Error

**Error**: `Qdrant is not available`

**Solution**:
```bash
# Check if Qdrant is running
docker compose ps

# Start Qdrant
docker compose up -d qdrant

# Verify Qdrant is accessible
curl http://localhost:6333/collections
```

#### 2. Module Import Error

**Error**: `ModuleNotFoundError: No module named 'main'`

**Solution**:
```bash
# Ensure you're in the api directory
cd api

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest test_main.py -v
```

#### 3. Test Failures Due to Existing Data

**Error**: Tests fail because of existing data in Qdrant

**Solution**:
```bash
# Delete Qdrant storage and restart
docker compose down
rm -rf qdrant_storage/
docker compose up -d

# Wait a moment for Qdrant to initialize
sleep 5

# Run tests
pytest test_main.py -v
```

#### 4. Port Already in Use

**Error**: Qdrant port 6333 is already in use

**Solution**:
```bash
# Find process using port
lsof -i :6333

# Kill the process or use different port in .env
# Then restart Qdrant
docker compose restart qdrant
```

#### 5. Slow Tests

**Issue**: Tests are running slowly

**Solution**:
```bash
# Run tests in parallel with pytest-xdist
pip install pytest-xdist

# Run with multiple workers
pytest test_main.py -n auto

# Run only fast tests
pytest test_main.py -m "not slow"
```

### Debug Mode

Run tests with detailed debugging:

```bash
# Show print statements and local variables
pytest test_main.py -s -l -vv

# Drop into debugger on failure
pytest test_main.py --pdb

# Show detailed traceback
pytest test_main.py --tb=long
```

### Logging

Enable logging in tests:

```python
import logging

def test_with_logging(caplog):
    """Test with logging enabled"""
    with caplog.at_level(logging.DEBUG):
        # Test code here
        pass
    
    # Check logs
    assert "Expected message" in caplog.text
```

## Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Qdrant Python Client](https://github.com/qdrant/qdrant-client)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

## Contributing

When adding new features:
1. Write tests for new functionality
2. Ensure all tests pass locally
3. Update this documentation if needed
4. Submit PR with test coverage

---

**Questions or Issues?**
Open an issue on GitHub or check the main README for contact information.
