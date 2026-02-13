"""FastMCP server for Yuque API integration.

This module provides an MCP server that exposes Yuque API functionality
as tools for AI assistants. It includes proper lifecycle management,
comprehensive error handling, and well-designed tool interfaces.

Tool Count: 13 tools (11 original + 2 file-based upload tools)
- Combined operations reduce API calls
- Removed dangerous/low-frequency operations
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from mcp.types import ToolAnnotations

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
_client: YuqueClient | None = None


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
            raise RuntimeError(f"Failed to initialize YuqueClient: {e}") from e
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


@mcp.tool(
    name="yuque_get_current_user",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def yuque_get_current_user() -> str:
    """Get authenticated user profile with stats (name, ID, repos count, followers)."""
    try:
        client = get_client()
        user = await client.get_current_user()
        return format_user(user)
    except YuqueAPIError as e:
        return f"✗ Error: {e.message}"


# =============================================================================
# Repository Tools (3 tools) - Optimized from 5
# =============================================================================


@mcp.tool(
    name="yuque_get_my_repositories",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def yuque_get_my_repositories(
    repo_type: str | None = None,
    offset: int = 0,
    limit: int = 20,
) -> str:
    """List user's repos with user info. repo_type: Book|Design, limit: max 100."""
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


@mcp.tool(
    name="yuque_get_repository_overview",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def yuque_get_repository_overview(repo_id: str) -> str:
    """Get repo details + full TOC structure. repo_id: ID (int) or namespace 'user/repo'."""
    try:
        client = get_client()
        repo, toc_items = await client.get_repository_overview(repo_id)

        output = format_repository(repo)
        output += "\n---\n\n"
        output += format_toc(toc_items)

        return output
    except YuqueAPIError as e:
        return f"✗ Error: {e.message}"


@mcp.tool(
    name="yuque_create_repository",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def yuque_create_repository(
    login: str,
    name: str,
    slug: str,
    description: str | None = None,
    public: int = 0,
) -> str:
    """Create repo under user/group (login). slug: URL path (alphanumeric/-). public: 0=private,1=public,2=internal."""
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
# File Helpers
# =============================================================================


def _read_markdown_file(file_path: str) -> tuple[str, str | None]:
    """Read a markdown file and extract title from first heading if present.

    Returns:
        Tuple of (content, extracted_title). extracted_title may be None.
    """
    path = Path(file_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not path.is_file():
        raise ValueError(f"Not a file: {path}")

    content = path.read_text(encoding="utf-8")

    # Try to extract title from first '# heading'
    title = None
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("# ") and not stripped.startswith("##"):
            title = stripped[2:].strip()
            break
        elif stripped:  # Non-empty, non-heading line found first
            break

    return content, title


# =============================================================================
# Document Tools (7 tools) - Includes file-based upload tools
# =============================================================================


@mcp.tool(
    name="yuque_list_documents",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def yuque_list_documents(
    repo_id: str,
    offset: int = 0,
    limit: int = 20,
) -> str:
    """List docs in repo with title, ID, slug, word count. limit: max 100."""
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


@mcp.tool(
    name="yuque_get_document",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def yuque_get_document(repo_id: str, doc_id: str) -> str:
    """Read document content + metadata. doc_id: ID (int) or slug string."""
    try:
        client = get_client()
        doc = await client.get_document(repo_id, doc_id)
        return format_document(doc)
    except YuqueAPIError as e:
        return f"✗ Error: {e.message}"


@mcp.tool(
    name="yuque_create_document_with_toc",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def yuque_create_document_with_toc(
    repo_id: str,
    title: str,
    body: str,
    format: str = "markdown",
    slug: str | None = None,
    public: int = 0,
    parent_uuid: str | None = None,
) -> str:
    """Create doc and auto-add to TOC. format: markdown|html|lake. parent_uuid: folder UUID or None for root."""
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


@mcp.tool(
    name="yuque_update_document",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def yuque_update_document(
    repo_id: str,
    doc_id: str,
    title: str | None = None,
    body: str | None = None,
    format: str | None = None,
    public: int | None = None,
) -> str:
    """Update doc fields (only provided params are changed). format: markdown|html|lake."""
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


@mcp.tool(
    name="yuque_delete_document",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def yuque_delete_document(repo_id: str, doc_id: str) -> str:
    """Delete document permanently (irreversible)."""
    try:
        client = get_client()
        doc = await client.delete_document(repo_id, doc_id)
        return (
            f"✓ Document deleted successfully!\n\n"
            f"Deleted: {doc.title} (ID: {doc.id})"
        )
    except YuqueAPIError as e:
        return f"✗ Error: {e.message}"


@mcp.tool(
    name="yuque_create_document_from_file",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
)
async def yuque_create_document_from_file(
    repo_id: str,
    file_path: str,
    title: str | None = None,
    slug: str | None = None,
    public: int = 0,
    parent_uuid: str | None = None,
) -> str:
    """Create doc from a local .md file and auto-add to TOC. Reads file content from file_path to avoid passing large body text. Title auto-extracted from first '# heading' if not provided."""
    try:
        content, extracted_title = _read_markdown_file(file_path)

        # Determine title: explicit > extracted from heading > filename
        if title is None:
            if extracted_title:
                title = extracted_title
            else:
                title = Path(file_path).stem

        client = get_client()
        data = DocumentCreate(
            title=title,
            body=content,
            format="markdown",
            slug=slug,
            public=public,
        )
        doc = await client.create_document(repo_id, data)
        await client.add_document_to_toc(repo_id, doc.id, parent_uuid)

        return (
            f"✓ Document created from file and added to TOC!\n\n"
            f"ID: {doc.id}\n"
            f"Title: {doc.title}\n"
            f"Slug: {doc.slug}\n"
            f"Source: {file_path}\n"
            f"TOC: Added successfully"
        )
    except (FileNotFoundError, ValueError) as e:
        return f"✗ File error: {e}"
    except YuqueAPIError as e:
        return f"✗ Error: {e.message}"


@mcp.tool(
    name="yuque_update_document_from_file",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
async def yuque_update_document_from_file(
    repo_id: str,
    doc_id: str,
    file_path: str,
    title: str | None = None,
    public: int | None = None,
) -> str:
    """Update doc content from a local .md file. Reads file content from file_path to avoid passing large body text. Title auto-extracted from first '# heading' if not provided."""
    try:
        content, extracted_title = _read_markdown_file(file_path)

        # Use extracted title only if no explicit title given
        effective_title = title if title is not None else extracted_title

        client = get_client()
        data = DocumentUpdate(
            title=effective_title,
            body=content,
            format="markdown",
            public=public,
        )
        doc = await client.update_document(repo_id, doc_id, data)
        updated = doc.updated_at.isoformat() if doc.updated_at else "N/A"
        return (
            f"✓ Document updated from file!\n\n"
            f"ID: {doc.id}\n"
            f"Title: {doc.title}\n"
            f"Source: {file_path}\n"
            f"Updated at: {updated}"
        )
    except (FileNotFoundError, ValueError) as e:
        return f"✗ File error: {e}"
    except YuqueAPIError as e:
        return f"✗ Error: {e.message}"


# =============================================================================
# TOC Tools (1 tool)
# =============================================================================


@mcp.tool(
    name="yuque_update_toc",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def yuque_update_toc(
    repo_id: str,
    action: str,
    action_mode: str,
    doc_ids: str | None = None,
    target_uuid: str | None = None,
    node_uuid: str | None = None,
    node_type: str | None = None,
    title: str | None = None,
    url: str | None = None,
    open_window: int | None = None,
    visible: int | None = None,
) -> str:
    """Modify TOC structure. To create a group/folder, use node_type='TITLE'. action: appendNode|prependNode|editNode|removeNode. action_mode: child|sibling."""
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


@mcp.tool(
    name="yuque_search_and_read",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def yuque_search_and_read(
    query: str,
    repo_id: str,
    read_first: bool = True,
) -> str:
    """Search docs in repo and optionally fetch first result's full content. query: max 200 chars."""
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
