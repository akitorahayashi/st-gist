import numpy as np
import pytest

from src.models.vector_store import VectorStore


@pytest.fixture
def vector_store():
    """Fixture for VectorStore."""
    return VectorStore(model_name="all-MiniLM-L6-v2")


def test_vector_store_initialization(vector_store):
    """Test VectorStore initialization."""
    assert vector_store.model is not None  # Model is loaded on initialization
    assert vector_store.texts == []
    assert vector_store.embeddings is None
    assert not vector_store.is_creating
    assert vector_store.last_error is None


def test_create_embeddings(vector_store):
    """Test creating embeddings from text."""
    text = "This is a test sentence. This is another test sentence."
    vector_store.create_embeddings(text)

    assert vector_store.model is not None
    assert not vector_store.is_creating
    assert vector_store.last_error is None
    assert len(vector_store.texts) > 0
    assert vector_store.embeddings is not None
    assert isinstance(vector_store.embeddings, np.ndarray)
    assert len(vector_store.texts) == len(vector_store.embeddings)


def test_search(vector_store):
    """Test searching for similar text."""
    text = "The quick brown fox jumps over the lazy dog."
    vector_store.create_embeddings(text)

    query = "A fast fox"
    results = vector_store.search(query, top_k=1)

    assert isinstance(results, str)
    assert "fox" in results


def test_search_with_no_embeddings(vector_store):
    """Test search when no embeddings are created."""
    query = "A fast fox"
    results = vector_store.search(query)
    assert results == ""


def test_reset(vector_store):
    """Test resetting the vector store."""
    text = "This is a test sentence."
    vector_store.create_embeddings(text)
    vector_store.reset()

    assert vector_store.texts == []
    assert vector_store.embeddings is None
    assert not vector_store.is_creating
    assert vector_store.last_error is None
