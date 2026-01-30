"""FastMCP server for Yuque API integration.

This module provides an MCP server that exposes Yuque API functionality
as tools for AI assistants. It includes proper lifecycle management,
comprehensive error handling, and well-designed tool interfaces.

Tool Count: 11 tools (optimized from 15)
- Combined operations reduce API calls
- Removed dangerous/low-frequency operations
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastmcp import FastMCP

from .client import YuqueClient
from .models import (
    DocumentCreate,
    DocumentUpdate,
    RepositoryCreate,
    YuqueAPIError,
    YuqueConfig,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global client instance (lazy initialization)
_client: Optional[YuqueClient] = None


def get_client() -> YuqueClient:
    """Get the global Yuque client instance (lazy initialization).

    Returns:
        The initialized YuqueClient.

    Raises:
        RuntimeError: If initialization fails.
    """
    global _client
    if _client is None:
        try:
            config = YuqueConfig()
            _client = YuqueClient(config)
            logger.info("Yuque client initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize Yuque client: %s", e)
            raise RuntimeError(f"Failed to initialize YuqueClient: {e}")
    return _client


# Initialize FastMCP server
mcp = FastMCP("Yuque MCP Server")


# =============================================================================
# Output Formatters
# =============================================================================


def format_user(user: Any) -> str:
    """Format user information for display."""
    return (
        f"👤 {user.name} (@{user.login})\n\n"
        f"**ID**: {user.id}\n"
        f"**Description**: {user.description or 'No description'}\n"
        f"**Knowledge Bases**: {user.books_count or 0}\n"
        f"**Public Knowledge Bases**: {user.public_books_count or 0}\n"
        f"**Followers**: {user.followers_count or 0}\n"
        f"**Following**: {user.following_count or 0}\n"
    )


def format_repository(repo: Any) -> str:
    """Format repository information for display."""
    return (
        f"# {repo.name}\n\n"
        f"**ID**: {repo.id}\n"
        f"**Namespace**: {repo.namespace}\n"
        f"**Slug**: {repo.slug}\n"
        f"**Type**: {repo.type}\n"
        f"**Description**: {repo.description or 'No description'}\n"
        f"**Visibility**: {'Public' if repo.public == 1 else 'Private'}\n"
        f"**Documents**: {repo.items_count or 0}\n"
    )


def format_document(doc: Any) -> str:
    """Format document information for display."""
    content = doc.body or doc.body_html or "(No content)"
    return (
        f"# {doc.title}\n\n"
        f"**ID**: {doc.id}\n"
        f"**Slug**: {doc.slug}\n"
        f"**Format**: {doc.format}\n"
        f"**Word Count**: {doc.word_count or 0}\n"
        f"**Visibility**: {'Public' if doc.public == 1 else 'Private'}\n\n"
        f"---\n\n{content}"
    )


def format_toc(toc_items: list[Any]) -> str:
    """Format table of contents for display."""
    if not toc_items:
        return "Table of contents is empty."

    output = "📑 Table of Contents\n\n"
    for item in toc_items:
        indent = "  " * ((item.level or 1) - 1)
        type_icon = {"DOC": "📄", "LINK": "🔗", "TITLE": "📁"}.get(item.type, "•")
        output += f"{indent}{type_icon} {item.title}\n"
        doc_id_str = item.doc_id if item.doc_id else ""
        output += f"{indent}   UUID: {item.uuid} | Doc ID: {doc_id_str}\n"

    return output


# =============================================================================
# User Tools (1 tool)
# =============================================================================


@mcp.tool()
async def get_current_user() -> str:
    """Get current authenticated user information.

    Returns:
        User profile with statistics including name, ID, and counts.
    """
    try:
        client = get_client()
        user = await client.get_current_user()
        return format_user(user)
    except YuqueAPIError as e:
        return f"✗ Error: {e.message}"


# =============================================================================
# Repository Tools (3 tools) - Optimized from 5
# =============================================================================


@mcp.tool()
async def get_my_repositories(
    repo_type: Optional[str] = None,
    offset: int = 0,
    limit: int = 20,
) -> str:
    """Get current user's knowledge bases (repositories).

    This combines user info and repository listing in one call.

    Args:
        repo_type: Filter by type: 'Book' or 'Design' (optional).
        offset: Pagination offset (default: 0).
        limit: Items per page, max 100 (default: 20).

    Returns:
        User info and list of repositories with names, IDs, and document counts.
    """
    try:
        client = get_client()
        user, repos, meta = await client.get_my_repositories(repo_type, offset, limit)

        output = format_user(user)
        output += "\n---\n\n"

        if not repos:
            output += "No repositories found."
            return output

        output += f"📚 My Repositories ({len(repos)} shown)\n\n"
        for i, repo in enumerate(repos, 1):
            output += f"{i}. **{repo.name}**\n"
            output += f"   ID: {repo.id} | Namespace: {repo.namespace}\n"
            output += f"   Documents: {repo.items_count or 0} | Type: {repo.type}\n\n"

        return output
    except YuqueAPIError as e:
        return f"✗ Error: {e.message}"


@mcp.tool()
async def get_repository_overview(repo_id: str) -> str:
    """Get repository details and its table of contents structure.

    This combines repository info and TOC in one call, providing a complete
    overview of the knowledge base.

    Args:
        repo_id: Repository ID or namespace (e.g., 'user/repo').

    Returns:
        Repository information and hierarchical TOC structure.
    """
    try:
        client = get_client()
        repo, toc_items = await client.get_repository_overview(repo_id)

        output = format_repository(repo)
        output += "\n---\n\n"
        output += format_toc(toc_items)

        return output
    except YuqueAPIError as e:
        return f"✗ Error: {e.message}"


@mcp.tool()
async def create_repository(
    login: str,
    name: str,
    slug: str,
    description: Optional[str] = None,
    public: int = 0,
) -> str:
    """Create a new knowledge base (repository).

    Args:
        login: User or group login/ID.
        name: Repository display name.
        slug: URL path identifier (alphanumeric and hyphens).
        description: Repository description (optional).
        public: Visibility: 0=private, 1=public, 2=internal (default: 0).

    Returns:
        Created repository details including ID and namespace.
    """
    try:
        client = get_client()
        data = RepositoryCreate(
            name=name,
            slug=slug,
            description=description,
            public=public,
        )
        repo = await client.create_repository(login, data)
        return (
            f"✓ Repository created successfully!\n\n"
            f"ID: {repo.id}\n"
            f"Name: {repo.name}\n"
            f"Namespace: {repo.namespace}\n"
            f"Slug: {repo.slug}"
        )
    except YuqueAPIError as e:
        return f"✗ Error: {e.message}"


# =============================================================================
# Document Tools (5 tools) - Optimized from 6
# =============================================================================


@mcp.tool()
async def list_documents(
    repo_id: str,
    offset: int = 0,
    limit: int = 20,
) -> str:
    """List all documents in a repository.

    Args:
        repo_id: Repository ID or namespace.
        offset: Pagination offset (default: 0).
        limit: Items per page, max 100 (default: 20).

    Returns:
        List of documents with titles, IDs, and metadata.
    """
    try:
        client = get_client()
        docs, meta = await client.list_documents(repo_id, offset, limit)
        total = meta.get("total", len(docs))

        if not docs:
            return "No documents found in this repository."

        output = f"📚 Documents in repository (Total: {total})\n\n"
        for i, doc in enumerate(docs, 1):
            output += f"{i}. **{doc.title}**\n"
            output += f"   ID: {doc.id} | Slug: {doc.slug}\n"
            updated = doc.updated_at.isoformat() if doc.updated_at else "N/A"
            output += f"   Words: {doc.word_count or 0} | Updated: {updated}\n\n"

        return output
    except YuqueAPIError as e:
        return f"✗ Error: {e.message}"


@mcp.tool()
async def get_document(repo_id: str, doc_id: str) -> str:
    """Retrieve a document's content and metadata.

    Args:
        repo_id: Repository ID or namespace.
        doc_id: Document ID or slug.

    Returns:
        Document content in markdown format with metadata.
    """
    try:
        client = get_client()
        doc = await client.get_document(repo_id, doc_id)
        return format_document(doc)
    except YuqueAPIError as e:
        return f"✗ Error: {e.message}"


@mcp.tool()
async def create_document_with_toc(
    repo_id: str,
    title: str,
    body: str,
    format: str = "markdown",
    slug: Optional[str] = None,
    public: int = 0,
    parent_uuid: Optional[str] = None,
) -> str:
    """Create a new document and automatically add it to the table of contents.

    This is the recommended way to create documents as it ensures they are
    visible in the repository's navigation.

    Args:
        repo_id: Repository ID or namespace.
        title: Document title.
        body: Document content.
        format: Content format: 'markdown', 'html', or 'lake' (default: 'markdown').
        slug: Custom URL path (optional).
        public: Visibility: 0=private, 1=public, 2=internal (default: 0).
        parent_uuid: Parent folder UUID in TOC (optional, adds to root if not specified).

    Returns:
        Created document details with TOC update confirmation.
    """
    try:
        client = get_client()

        # Create the document
        data = DocumentCreate(
            title=title,
            body=body,
            format=format,
            slug=slug,
            public=public,
        )
        doc = await client.create_document(repo_id, data)

        # Add to TOC
        await client.add_document_to_toc(repo_id, doc.id, parent_uuid)

        return (
            f"✓ Document created and added to TOC!\n\n"
            f"ID: {doc.id}\n"
            f"Title: {doc.title}\n"
            f"Slug: {doc.slug}\n"
            f"TOC: Added successfully"
        )
    except YuqueAPIError as e:
        return f"✗ Error: {e.message}"


@mcp.tool()
async def update_document(
    repo_id: str,
    doc_id: str,
    title: Optional[str] = None,
    body: Optional[str] = None,
    format: Optional[str] = None,
    public: Optional[int] = None,
) -> str:
    """Update an existing document.

    Args:
        repo_id: Repository ID or namespace.
        doc_id: Document ID or slug.
        title: New title (optional).
        body: New content (optional).
        format: New content format (optional).
        public: New visibility setting (optional).

    Returns:
        Updated document confirmation.
    """
    try:
        client = get_client()
        data = DocumentUpdate(
            title=title,
            body=body,
            format=format,
            public=public,
        )
        doc = await client.update_document(repo_id, doc_id, data)
        updated = doc.updated_at.isoformat() if doc.updated_at else "N/A"
        return (
            f"✓ Document updated successfully!\n\n"
            f"ID: {doc.id}\n"
            f"Title: {doc.title}\n"
            f"Updated at: {updated}"
        )
    except YuqueAPIError as e:
        return f"✗ Error: {e.message}"


@mcp.tool()
async def delete_document(repo_id: str, doc_id: str) -> str:
    """Delete a document.

    Warning: This action is irreversible.

    Args:
        repo_id: Repository ID or namespace.
        doc_id: Document ID or slug.

    Returns:
        Deletion confirmation.
    """
    try:
        client = get_client()
        doc = await client.delete_document(repo_id, doc_id)
        return (
            f"✓ Document deleted successfully!\n\n"
            f"Deleted: {doc.title} (ID: {doc.id})"
        )
    except YuqueAPIError as e:
        return f"✗ Error: {e.message}"


# =============================================================================
# TOC Tools (1 tool)
# =============================================================================


@mcp.tool()
async def update_toc(
    repo_id: str,
    action: str,
    action_mode: str,
    doc_ids: Optional[str] = None,
    target_uuid: Optional[str] = None,
    node_uuid: Optional[str] = None,
    node_type: Optional[str] = None,
    title: Optional[str] = None,
    url: Optional[str] = None,
    open_window: Optional[int] = None,
    visible: Optional[int] = None,
) -> str:
    """Update repository table of contents (add/move/remove documents).

    Args:
        repo_id: Repository ID or namespace.
        action: Action type: 'appendNode', 'prependNode', 'editNode', 'removeNode'.
        action_mode: Position mode: 'sibling' or 'child'.
        doc_ids: Comma-separated document IDs to add (for appendNode/prependNode).
        target_uuid: Target node UUID for positioning (optional).
        node_uuid: Node UUID to operate on (for editNode/removeNode).
        node_type: Node type: 'DOC', 'LINK', 'TITLE' (optional).
        title: Node title for TITLE type nodes (optional).
        url: Link URL for LINK type nodes (optional).
        open_window: Open in new window: 0=same page, 1=new window (optional).
        visible: Visibility: 0=hidden, 1=visible (optional).

    Returns:
        TOC update confirmation.

    Examples:
        Add document to root:
            update_toc(repo_id='123', action='appendNode', action_mode='child',
                      doc_ids='456', node_type='DOC')

        Add document under a folder:
            update_toc(repo_id='123', action='appendNode', action_mode='child',
                      doc_ids='456', target_uuid='folder-uuid', node_type='DOC')

        Create a folder:
            update_toc(repo_id='123', action='appendNode', action_mode='child',
                      node_type='TITLE', title='New Folder')

        Create external link:
            update_toc(repo_id='123', action='appendNode', action_mode='child',
                      node_type='LINK', title='Google', url='https://google.com', open_window=1)
    """
    try:
        client = get_client()

        # Parse doc_ids string to list
        doc_id_list = None
        if doc_ids:
            doc_id_list = [int(id.strip()) for id in doc_ids.split(",")]

        await client.update_toc(
            repo_id=repo_id,
            action=action,
            action_mode=action_mode,
            doc_ids=doc_id_list,
            target_uuid=target_uuid,
            node_uuid=node_uuid,
            node_type=node_type,
            title=title,
            url=url,
            open_window=open_window,
            visible=visible,
        )

        return (
            f"✓ Table of contents updated successfully!\n\n"
            f"Action: {action}\n"
            f"Mode: {action_mode}"
        )
    except YuqueAPIError as e:
        return f"✗ Error: {e.message}"


# =============================================================================
# Search Tools (1 tool) - Optimized
# =============================================================================


@mcp.tool()
async def search_and_read(
    query: str,
    repo_id: str,
    read_first: bool = True,
) -> str:
    """Search for documents and optionally read the first result.

    This combines search and document retrieval in one call. When you search,
    you usually want to read the content of the top result.

    Args:
        query: Search keywords (max 200 characters).
        repo_id: Repository ID or namespace to search within.
        read_first: Whether to read the first matching document (default: True).

    Returns:
        Search results and optionally the content of the first matched document.
    """
    try:
        client = get_client()
        results, first_doc, meta = await client.search_and_read(
            query=query,
            repo_id=repo_id,
            read_first=read_first,
        )
        total = meta.get("total", len(results))

        if not results:
            return f"No documents found matching '{query}'."

        output = f"🔍 Search results for '{query}' ({total} found)\n\n"
        for i, item in enumerate(results, 1):
            marker = "→ " if i == 1 and read_first else ""
            output += f"{marker}{i}. **{item.title}**\n"
            output += f"   Type: {item.type} | URL: {item.url}\n"
            if item.summary:
                output += f"   Summary: {item.summary}\n"
            output += "\n"

        if first_doc:
            output += "\n---\n\n"
            output += "📄 First Result Content:\n\n"
            output += format_document(first_doc)

        return output
    except YuqueAPIError as e:
        return f"✗ Error: {e.message}"


# =============================================================================
# Server Entry Point
# =============================================================================


def main() -> None:
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
