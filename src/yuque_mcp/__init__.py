"""Yuque MCP Server - Model Context Protocol server for Yuque API integration.

This package provides an MCP server that enables AI assistants to interact
with Yuque (语雀) knowledge bases through a standardized protocol.

Example:
    Run the server directly:
        $ python -m yuque_mcp.server

    Or use the installed script:
        $ yuque-mcp

    Configure in Claude Desktop or Claude Code CLI to use the tools.
"""

from .client import YuqueClient
from .models import (
    ContentFormat,
    Document,
    DocumentCreate,
    DocumentUpdate,
    Repository,
    RepositoryCreate,
    RepositoryUpdate,
    SearchResult,
    SearchType,
    TocAction,
    TocActionMode,
    TocNode,
    TocNodeType,
    User,
    Visibility,
    YuqueAPIError,
    YuqueConfig,
)
from .server import mcp

__version__ = "0.2.0"
__author__ = "yuque-mcp contributors"
__license__ = "MIT"

__all__ = [
    # Server
    "mcp",
    # Client
    "YuqueClient",
    # Configuration
    "YuqueConfig",
    "YuqueAPIError",
    # Enums
    "ContentFormat",
    "Visibility",
    "TocNodeType",
    "TocAction",
    "TocActionMode",
    "SearchType",
    # Models
    "User",
    "Repository",
    "RepositoryCreate",
    "RepositoryUpdate",
    "Document",
    "DocumentCreate",
    "DocumentUpdate",
    "TocNode",
    "SearchResult",
]
