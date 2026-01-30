"""Test fixtures and configuration for pytest."""

import pytest

from yuque_mcp.models import YuqueConfig


@pytest.fixture
def mock_config() -> YuqueConfig:
    """Create a mock Yuque configuration."""
    return YuqueConfig(
        api_token="test_token_123",
        base_url="https://www.yuque.com",
    )


@pytest.fixture
def mock_user_response() -> dict:
    """Mock user API response."""
    return {
        "data": {
            "id": 12345,
            "login": "testuser",
            "name": "Test User",
            "avatar_url": "https://example.com/avatar.png",
            "description": "Test description",
            "books_count": 5,
            "public_books_count": 2,
            "followers_count": 10,
            "following_count": 5,
        }
    }


@pytest.fixture
def mock_repository_response() -> dict:
    """Mock repository API response."""
    return {
        "data": {
            "id": 67890,
            "type": "Book",
            "slug": "test-repo",
            "name": "Test Repository",
            "user_id": 12345,
            "description": "A test repository",
            "public": 0,
            "items_count": 10,
            "namespace": "testuser/test-repo",
        }
    }


@pytest.fixture
def mock_document_response() -> dict:
    """Mock document API response."""
    return {
        "data": {
            "id": 11111,
            "slug": "test-doc",
            "title": "Test Document",
            "book_id": 67890,
            "user_id": 12345,
            "format": "markdown",
            "body": "# Test\n\nThis is test content.",
            "public": 0,
            "word_count": 5,
        }
    }


@pytest.fixture
def mock_toc_response() -> dict:
    """Mock TOC API response."""
    return {
        "data": [
            {
                "uuid": "uuid-1",
                "type": "TITLE",
                "title": "Getting Started",
                "level": 1,
                "visible": 1,
            },
            {
                "uuid": "uuid-2",
                "type": "DOC",
                "title": "Introduction",
                "doc_id": 11111,
                "level": 2,
                "visible": 1,
            },
        ]
    }
