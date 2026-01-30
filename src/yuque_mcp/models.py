"""Pydantic models for Yuque API configuration and data structures.

This module provides type-safe data models for all Yuque API entities,
ensuring proper validation and serialization of API responses.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# =============================================================================
# Configuration
# =============================================================================


class YuqueConfig(BaseSettings):
    """Configuration for Yuque API connection.

    Reads configuration from environment variables with YUQUE_ prefix.

    Attributes:
        api_token: Yuque API token for authentication.
        base_url: Base URL for Yuque API (default: https://www.yuque.com).

    Example:
        Set environment variables:
            YUQUE_API_TOKEN=your_token_here
            YUQUE_BASE_URL=https://www.yuque.com

        Or use a .env file in the project root.
    """

    model_config = SettingsConfigDict(
        env_prefix="YUQUE_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    api_token: str = Field(..., description="Yuque API token for authentication")
    base_url: str = Field(
        default="https://www.yuque.com",
        description="Yuque API base URL",
    )


# =============================================================================
# Exceptions
# =============================================================================


class YuqueAPIError(Exception):
    """Custom exception for Yuque API errors.

    Attributes:
        status_code: HTTP status code from the API response.
        message: Human-readable error message.
        details: Additional error details from the API response.
    """

    def __init__(
        self,
        status_code: int,
        message: str,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        self.status_code = status_code
        self.message = message
        self.details = details or {}
        super().__init__(f"Yuque API Error {status_code}: {message}")


# =============================================================================
# Enums
# =============================================================================


class ContentFormat(str, Enum):
    """Document content format types."""

    MARKDOWN = "markdown"
    HTML = "html"
    LAKE = "lake"


class Visibility(int, Enum):
    """Content visibility levels."""

    PRIVATE = 0
    PUBLIC = 1
    INTERNAL = 2


class TocNodeType(str, Enum):
    """Table of contents node types."""

    DOC = "DOC"
    LINK = "LINK"
    TITLE = "TITLE"


class TocAction(str, Enum):
    """TOC update action types."""

    APPEND_NODE = "appendNode"
    PREPEND_NODE = "prependNode"
    EDIT_NODE = "editNode"
    REMOVE_NODE = "removeNode"


class TocActionMode(str, Enum):
    """TOC action mode types."""

    SIBLING = "sibling"
    CHILD = "child"


class SearchType(str, Enum):
    """Search target types."""

    DOC = "doc"
    REPO = "repo"


class RepoType(str, Enum):
    """Repository types."""

    BOOK = "Book"
    DESIGN = "Design"


# =============================================================================
# Base Models
# =============================================================================


class YuqueBaseModel(BaseModel):
    """Base model with common configuration for all Yuque models."""

    model_config = {"extra": "ignore", "populate_by_name": True}


# =============================================================================
# User Models
# =============================================================================


class User(YuqueBaseModel):
    """Yuque user model.

    Represents a user account on Yuque platform.
    """

    id: int = Field(..., description="User ID")
    login: str = Field(..., description="User login name (username)")
    name: str = Field(..., description="User display name")
    avatar_url: Optional[str] = Field(None, description="User avatar URL")
    description: Optional[str] = Field(None, description="User bio/description")
    books_count: Optional[int] = Field(None, description="Total knowledge bases count")
    public_books_count: Optional[int] = Field(
        None, description="Public knowledge bases count"
    )
    followers_count: Optional[int] = Field(None, description="Followers count")
    following_count: Optional[int] = Field(None, description="Following count")
    created_at: Optional[datetime] = Field(None, description="Account creation time")
    updated_at: Optional[datetime] = Field(None, description="Last update time")


# =============================================================================
# Repository Models
# =============================================================================


class Repository(YuqueBaseModel):
    """Yuque repository (knowledge base) model.

    Represents a knowledge base that contains documents.
    """

    id: int = Field(..., description="Repository ID")
    type: str = Field(..., description="Repository type (Book, Design)")
    slug: str = Field(..., description="Repository slug for URL")
    name: str = Field(..., description="Repository name")
    user_id: int = Field(..., description="Owner user ID")
    description: Optional[str] = Field(None, description="Repository description")
    public: int = Field(default=0, description="Visibility level (0=private)")
    items_count: Optional[int] = Field(None, description="Document count")
    namespace: Optional[str] = Field(
        None, description="Full namespace (user/repo)"
    )
    created_at: Optional[datetime] = Field(None, description="Creation time")
    updated_at: Optional[datetime] = Field(None, description="Last update time")


class RepositoryCreate(YuqueBaseModel):
    """Model for creating a new repository."""

    name: str = Field(..., description="Repository name")
    slug: str = Field(..., description="Repository slug for URL")
    description: Optional[str] = Field(None, description="Repository description")
    public: int = Field(default=0, description="Visibility level")
    enhancedPrivacy: Optional[bool] = Field(
        None, description="Enhanced privacy - excludes team members except admins"
    )


class RepositoryUpdate(YuqueBaseModel):
    """Model for updating a repository."""

    name: Optional[str] = Field(None, description="New repository name")
    slug: Optional[str] = Field(None, description="New repository slug")
    description: Optional[str] = Field(None, description="New description")
    public: Optional[int] = Field(None, description="New visibility level")


# =============================================================================
# Document Models
# =============================================================================


class Document(YuqueBaseModel):
    """Yuque document model.

    Represents a document within a repository.
    """

    id: int = Field(..., description="Document ID")
    slug: str = Field(..., description="Document slug for URL")
    title: str = Field(..., description="Document title")
    book_id: int = Field(..., description="Parent repository ID")
    user_id: int = Field(..., description="Author user ID")
    format: Optional[str] = Field(None, description="Content format")
    body: Optional[str] = Field(None, description="Document content (raw)")
    body_draft: Optional[str] = Field(None, description="Draft content")
    body_html: Optional[str] = Field(None, description="HTML rendered content")
    body_lake: Optional[str] = Field(None, description="Lake format content")
    public: int = Field(default=0, description="Visibility level")
    status: Optional[int] = Field(None, description="Document status")
    word_count: Optional[int] = Field(None, description="Word count")
    cover: Optional[str] = Field(None, description="Cover image URL")
    description: Optional[str] = Field(None, description="Document description")
    created_at: Optional[datetime] = Field(None, description="Creation time")
    updated_at: Optional[datetime] = Field(None, description="Last update time")


class DocumentCreate(YuqueBaseModel):
    """Model for creating a new document."""

    title: str = Field(..., description="Document title")
    body: str = Field(..., description="Document content")
    format: str = Field(default="markdown", description="Content format")
    slug: Optional[str] = Field(None, description="Custom slug for URL")
    public: int = Field(default=0, description="Visibility level")


class DocumentUpdate(YuqueBaseModel):
    """Model for updating a document."""

    title: Optional[str] = Field(None, description="New title")
    body: Optional[str] = Field(None, description="New content")
    format: Optional[str] = Field(None, description="New format")
    public: Optional[int] = Field(None, description="New visibility level")


# =============================================================================
# TOC Models
# =============================================================================


class TocNode(YuqueBaseModel):
    """Table of contents node model.

    Represents a single node in the repository's table of contents.
    """

    uuid: str = Field(..., description="Node unique identifier")
    type: str = Field(..., description="Node type (DOC, LINK, TITLE)")
    title: str = Field(..., description="Node title")
    url: Optional[str] = Field(None, description="Link URL (for LINK type)")
    slug: Optional[str] = Field(None, description="Node URL slug (deprecated)")
    doc_id: Optional[int] = Field(None, description="Document ID (for DOC type)")
    id: Optional[int] = Field(None, description="Document ID (deprecated, use doc_id)")
    level: Optional[int] = Field(None, description="Nesting level (1-based)")
    depth: Optional[int] = Field(None, description="Nesting level (deprecated, use level)")
    visible: int = Field(default=1, description="Visibility flag (0=hidden, 1=visible)")
    open_window: int = Field(default=0, description="Open in new window (0=same, 1=new)")
    parent_uuid: Optional[str] = Field(None, description="Parent node UUID")
    child_uuid: Optional[str] = Field(None, description="First child node UUID")
    sibling_uuid: Optional[str] = Field(None, description="Next sibling node UUID")
    prev_uuid: Optional[str] = Field(None, description="Previous sibling node UUID")

    @field_validator("doc_id", mode="before")
    @classmethod
    def parse_doc_id(cls, v: Any) -> Optional[int]:
        """Handle empty string from API as None."""
        if v == "" or v is None:
            return None
        return int(v)

    @field_validator("id", mode="before")
    @classmethod
    def parse_id(cls, v: Any) -> Optional[int]:
        """Handle empty string from API as None."""
        if v == "" or v is None:
            return None
        return int(v)


class TocUpdateRequest(YuqueBaseModel):
    """Model for updating table of contents."""

    action: TocAction = Field(..., description="Action to perform")
    action_mode: TocActionMode = Field(..., description="Action mode")
    doc_ids: Optional[list[int]] = Field(None, description="Document IDs to add")
    target_uuid: Optional[str] = Field(None, description="Target node UUID")
    node_uuid: Optional[str] = Field(None, description="Node UUID to operate on")
    type: Optional[TocNodeType] = Field(None, description="Node type")
    title: Optional[str] = Field(None, description="Node title")
    url: Optional[str] = Field(None, description="Link URL")
    open_window: Optional[int] = Field(None, description="Open in new window (0=same, 1=new)")
    visible: Optional[int] = Field(None, description="Visibility (0=hidden, 1=visible)")


# =============================================================================
# Search Models
# =============================================================================


class SearchResult(YuqueBaseModel):
    """Search result model.

    Represents a single search result item.
    """

    id: int = Field(..., description="Result item ID")
    type: str = Field(..., description="Result type (doc or repo)")
    title: str = Field(..., description="Result title")
    summary: Optional[str] = Field(None, description="Result summary/snippet")
    url: str = Field(..., description="Result URL")
    info: Optional[str] = Field(None, description="Additional info")
    target: Optional[dict[str, Any]] = Field(None, description="Target doc or repo object")


# =============================================================================
# API Response Wrappers
# =============================================================================


class APIResponse(YuqueBaseModel):
    """Generic API response wrapper."""

    data: Any = Field(..., description="Response data")


class PaginatedResponse(YuqueBaseModel):
    """Paginated API response wrapper."""

    data: list[Any] = Field(default_factory=list, description="Response data list")
    meta: Optional[dict[str, Any]] = Field(None, description="Pagination metadata")
