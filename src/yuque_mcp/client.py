"""Yuque API client with authentication, error handling, and lifecycle management.

This module provides an async HTTP client for interacting with the Yuque API,
with proper resource management and comprehensive error handling.
"""

from __future__ import annotations

import logging
from types import TracebackType
from typing import Any, Optional, Union

import httpx

from .models import (
    Document,
    DocumentCreate,
    DocumentUpdate,
    Repository,
    RepositoryCreate,
    RepositoryUpdate,
    SearchResult,
    TocNode,
    User,
    YuqueAPIError,
    YuqueConfig,
)

# Configure module logger
logger = logging.getLogger(__name__)

# HTTP status code to error message mapping
ERROR_MESSAGES: dict[int, str] = {
    400: "请求参数非法 (Invalid request parameters)",
    401: "Token/Scope 未通过鉴权 (Authentication failed)",
    403: "无操作权限 (Permission denied)",
    404: "实体未找到 (Entity not found)",
    422: "请求参数校验失败 (Validation failed)",
    429: "访问频率超限 (Rate limit exceeded)",
    500: "内部错误 (Internal server error)",
}


class YuqueClient:
    """Async HTTP client for Yuque API with proper lifecycle management.

    This client handles authentication, request/response processing, and
    error handling for all Yuque API operations.

    Attributes:
        config: Yuque API configuration.
        base_url: Base URL for API requests.

    Example:
        Using as async context manager (recommended):

            async with YuqueClient(config) as client:
                user = await client.get_current_user()
                print(user.name)

        Manual lifecycle management:

            client = YuqueClient(config)
            try:
                user = await client.get_current_user()
            finally:
                await client.close()
    """

    def __init__(self, config: YuqueConfig) -> None:
        """Initialize the Yuque API client.

        Args:
            config: Yuque API configuration with token and base URL.
        """
        self.config = config
        self.base_url = config.base_url
        self._client: Optional[httpx.AsyncClient] = None
        logger.debug("YuqueClient initialized with base_url=%s", self.base_url)

    @property
    def _http_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client instance."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "X-Auth-Token": self.config.api_token,
                    "Content-Type": "application/json",
                    "User-Agent": "yuque-mcp/0.2.0",
                },
                timeout=30.0,
            )
            logger.debug("Created new httpx.AsyncClient")
        return self._client

    async def close(self) -> None:
        """Close the HTTP client and release resources.

        This method should be called when the client is no longer needed
        to properly release network resources.
        """
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            logger.debug("Closed httpx.AsyncClient")
        self._client = None

    async def __aenter__(self) -> "YuqueClient":
        """Enter async context manager."""
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """Exit async context manager and close resources."""
        await self.close()

    def _handle_error(self, response: httpx.Response) -> None:
        """Handle HTTP error responses.

        Args:
            response: The HTTP response to check for errors.

        Raises:
            YuqueAPIError: If the response indicates an error.
        """
        status_code = response.status_code

        try:
            error_data = response.json()
            message = error_data.get("message", response.text)
            details = error_data
        except Exception:
            message = response.text
            details = {}

        error_msg = ERROR_MESSAGES.get(status_code, message)
        logger.error(
            "API error: status=%d, message=%s, details=%s",
            status_code,
            error_msg,
            details,
        )
        raise YuqueAPIError(status_code, error_msg, details)

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[dict[str, Any]] = None,
        json: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Make an HTTP request to the Yuque API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE).
            path: API endpoint path.
            params: Query parameters.
            json: JSON request body.

        Returns:
            Parsed JSON response.

        Raises:
            YuqueAPIError: If the request fails or returns an error.
        """
        logger.debug("Request: %s %s params=%s", method, path, params)

        try:
            response = await self._http_client.request(
                method=method,
                url=path,
                params=params,
                json=json,
            )

            if response.status_code >= 400:
                self._handle_error(response)

            return response.json()

        except httpx.HTTPError as e:
            logger.exception("HTTP request failed: %s", str(e))
            raise YuqueAPIError(500, f"HTTP request failed: {str(e)}")

    # =========================================================================
    # User Operations
    # =========================================================================

    async def get_current_user(self) -> User:
        """Get the current authenticated user.

        Returns:
            User object with profile information.

        Raises:
            YuqueAPIError: If the request fails.
        """
        result = await self._request("GET", "/api/v2/user")
        return User(**result.get("data", {}))

    # =========================================================================
    # Repository Operations
    # =========================================================================

    async def list_repositories(
        self,
        login: str,
        repo_type: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Repository], dict[str, Any]]:
        """List repositories for a user or group.

        Args:
            login: User or group login name.
            repo_type: Filter by repository type ('Book' or 'Design').
            offset: Pagination offset.
            limit: Number of items per page (max 100).

        Returns:
            Tuple of (list of Repository objects, pagination metadata).

        Raises:
            YuqueAPIError: If the request fails.
        """
        params: dict[str, Any] = {"offset": offset, "limit": limit}
        if repo_type:
            params["type"] = repo_type

        result = await self._request(
            "GET", f"/api/v2/users/{login}/repos", params=params
        )

        repos = [Repository(**repo) for repo in result.get("data", [])]
        meta = result.get("meta", {})
        return repos, meta

    async def get_repository(self, repo_id: Union[int, str]) -> Repository:
        """Get repository details.

        Args:
            repo_id: Repository ID or namespace (e.g., 'user/repo').

        Returns:
            Repository object with details.

        Raises:
            YuqueAPIError: If the request fails or repository not found.
        """
        result = await self._request("GET", f"/api/v2/repos/{repo_id}")
        return Repository(**result.get("data", {}))

    async def create_repository(
        self,
        login: str,
        data: RepositoryCreate,
    ) -> Repository:
        """Create a new repository.

        Args:
            login: User or group login name.
            data: Repository creation data.

        Returns:
            Created Repository object.

        Raises:
            YuqueAPIError: If the request fails.
        """
        result = await self._request(
            "POST",
            f"/api/v2/users/{login}/repos",
            json=data.model_dump(exclude_none=True),
        )
        return Repository(**result.get("data", {}))

    async def update_repository(
        self,
        repo_id: Union[int, str],
        data: RepositoryUpdate,
    ) -> Repository:
        """Update a repository.

        Args:
            repo_id: Repository ID or namespace.
            data: Repository update data.

        Returns:
            Updated Repository object.

        Raises:
            YuqueAPIError: If the request fails.
        """
        result = await self._request(
            "PUT",
            f"/api/v2/repos/{repo_id}",
            json=data.model_dump(exclude_none=True),
        )
        return Repository(**result.get("data", {}))

    async def delete_repository(self, repo_id: Union[int, str]) -> Repository:
        """Delete a repository.

        Args:
            repo_id: Repository ID or namespace.

        Returns:
            Deleted Repository object.

        Raises:
            YuqueAPIError: If the request fails.
        """
        result = await self._request("DELETE", f"/api/v2/repos/{repo_id}")
        return Repository(**result.get("data", {}))

    # =========================================================================
    # Document Operations
    # =========================================================================

    async def list_documents(
        self,
        repo_id: Union[int, str],
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Document], dict[str, Any]]:
        """List documents in a repository.

        Args:
            repo_id: Repository ID or namespace.
            offset: Pagination offset.
            limit: Number of items per page (max 100).

        Returns:
            Tuple of (list of Document objects, pagination metadata).

        Raises:
            YuqueAPIError: If the request fails.
        """
        result = await self._request(
            "GET",
            f"/api/v2/repos/{repo_id}/docs",
            params={"offset": offset, "limit": limit},
        )

        docs = [Document(**doc) for doc in result.get("data", [])]
        meta = result.get("meta", {})
        return docs, meta

    async def get_document(
        self,
        repo_id: Union[int, str],
        doc_id: Union[int, str],
    ) -> Document:
        """Get document details and content.

        Args:
            repo_id: Repository ID or namespace.
            doc_id: Document ID or slug.

        Returns:
            Document object with content.

        Raises:
            YuqueAPIError: If the request fails or document not found.
        """
        result = await self._request(
            "GET", f"/api/v2/repos/{repo_id}/docs/{doc_id}"
        )
        return Document(**result.get("data", {}))

    async def create_document(
        self,
        repo_id: Union[int, str],
        data: DocumentCreate,
    ) -> Document:
        """Create a new document.

        Note: After creating a document, call update_toc() to add it
        to the repository's table of contents.

        Args:
            repo_id: Repository ID or namespace.
            data: Document creation data.

        Returns:
            Created Document object.

        Raises:
            YuqueAPIError: If the request fails.
        """
        result = await self._request(
            "POST",
            f"/api/v2/repos/{repo_id}/docs",
            json=data.model_dump(exclude_none=True),
        )
        return Document(**result.get("data", {}))

    async def update_document(
        self,
        repo_id: Union[int, str],
        doc_id: Union[int, str],
        data: DocumentUpdate,
    ) -> Document:
        """Update a document.

        Args:
            repo_id: Repository ID or namespace.
            doc_id: Document ID or slug.
            data: Document update data.

        Returns:
            Updated Document object.

        Raises:
            YuqueAPIError: If the request fails.
        """
        result = await self._request(
            "PUT",
            f"/api/v2/repos/{repo_id}/docs/{doc_id}",
            json=data.model_dump(exclude_none=True),
        )
        return Document(**result.get("data", {}))

    async def delete_document(
        self,
        repo_id: Union[int, str],
        doc_id: Union[int, str],
    ) -> Document:
        """Delete a document.

        Args:
            repo_id: Repository ID or namespace.
            doc_id: Document ID or slug.

        Returns:
            Deleted Document object.

        Raises:
            YuqueAPIError: If the request fails.
        """
        result = await self._request(
            "DELETE", f"/api/v2/repos/{repo_id}/docs/{doc_id}"
        )
        return Document(**result.get("data", {}))

    # =========================================================================
    # TOC Operations
    # =========================================================================

    async def get_toc(self, repo_id: Union[int, str]) -> list[TocNode]:
        """Get repository table of contents.

        Args:
            repo_id: Repository ID or namespace.

        Returns:
            List of TocNode objects representing the TOC structure.

        Raises:
            YuqueAPIError: If the request fails.
        """
        result = await self._request("GET", f"/api/v2/repos/{repo_id}/toc")
        return [TocNode(**item) for item in result.get("data", [])]

    async def update_toc(
        self,
        repo_id: Union[int, str],
        action: str,
        action_mode: str,
        doc_ids: Optional[list[int]] = None,
        target_uuid: Optional[str] = None,
        node_uuid: Optional[str] = None,
        node_type: Optional[str] = None,
        title: Optional[str] = None,
        url: Optional[str] = None,
        open_window: Optional[int] = None,
        visible: Optional[int] = None,
    ) -> dict[str, Any]:
        """Update repository table of contents.

        Args:
            repo_id: Repository ID or namespace.
            action: Action type ('appendNode', 'prependNode', 'editNode', 'removeNode').
            action_mode: Mode ('sibling' or 'child').
            doc_ids: List of document IDs to add.
            target_uuid: Target node UUID.
            node_uuid: Node UUID to operate on.
            node_type: Node type ('DOC', 'LINK', 'TITLE').
            title: Node title.
            url: Link URL (for LINK type).
            open_window: Open in new window (0=same page, 1=new window).
            visible: Visibility (0=hidden, 1=visible).

        Returns:
            API response data.

        Raises:
            YuqueAPIError: If the request fails.
        """
        data: dict[str, Any] = {
            "action": action,
            "action_mode": action_mode,
        }

        if doc_ids is not None:
            data["doc_ids"] = doc_ids
        if target_uuid is not None:
            data["target_uuid"] = target_uuid
        if node_uuid is not None:
            data["node_uuid"] = node_uuid
        if node_type is not None:
            data["type"] = node_type
        if title is not None:
            data["title"] = title
        if url is not None:
            data["url"] = url
        if open_window is not None:
            data["open_window"] = open_window
        if visible is not None:
            data["visible"] = visible

        return await self._request("PUT", f"/api/v2/repos/{repo_id}/toc", json=data)

    async def add_document_to_toc(
        self,
        repo_id: Union[int, str],
        doc_id: int,
        parent_uuid: Optional[str] = None,
    ) -> dict[str, Any]:
        """Convenience method to add a document to the TOC.

        Args:
            repo_id: Repository ID or namespace.
            doc_id: Document ID to add.
            parent_uuid: Parent node UUID (if None, adds to root).

        Returns:
            API response data.

        Raises:
            YuqueAPIError: If the request fails.
        """
        return await self.update_toc(
            repo_id=repo_id,
            action="appendNode",
            action_mode="child",
            doc_ids=[doc_id],
            target_uuid=parent_uuid,
            node_type="DOC",
        )

    # =========================================================================
    # Combined Operations (for MCP tool optimization)
    # =========================================================================

    async def get_my_repositories(
        self,
        repo_type: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[User, list[Repository], dict[str, Any]]:
        """Get current user info and their repositories in one call.

        This method combines get_current_user and list_repositories to reduce
        the number of API calls needed when viewing the user's knowledge bases.

        Args:
            repo_type: Filter by repository type ('Book' or 'Design').
            offset: Pagination offset.
            limit: Number of items per page (max 100).

        Returns:
            Tuple of (User object, list of Repository objects, pagination metadata).

        Raises:
            YuqueAPIError: If the request fails.
        """
        user = await self.get_current_user()
        repos, meta = await self.list_repositories(user.login, repo_type, offset, limit)
        return user, repos, meta

    async def get_repository_overview(
        self,
        repo_id: Union[int, str],
    ) -> tuple[Repository, list[TocNode]]:
        """Get repository details and its table of contents in one call.

        This method combines get_repository and get_toc to provide a complete
        overview of a knowledge base including its structure.

        Args:
            repo_id: Repository ID or namespace (e.g., 'user/repo').

        Returns:
            Tuple of (Repository object, list of TocNode objects).

        Raises:
            YuqueAPIError: If the request fails.
        """
        repo = await self.get_repository(repo_id)
        toc = await self.get_toc(repo_id)
        return repo, toc

    async def search_and_read(
        self,
        query: str,
        repo_id: Union[int, str],
        read_first: bool = True,
    ) -> tuple[list[SearchResult], Optional[Document], dict[str, Any]]:
        """Search for documents and optionally read the first result.

        This method combines search and get_document to provide search
        results along with the content of the top result.

        Args:
            query: Search keywords (max 200 characters).
            repo_id: Repository ID or namespace to search within.
            read_first: Whether to read the first matching document (default: True).

        Returns:
            Tuple of (list of SearchResult objects, first Document or None, metadata).

        Raises:
            YuqueAPIError: If the request fails.
        """
        # Search within the specific repository
        results, meta = await self.search(
            query=query,
            search_type="doc",
            scope=str(repo_id),
            page=1,
        )

        first_doc = None
        if read_first and results:
            # Extract doc_id from the first result
            first_result = results[0]
            if first_result.id:
                try:
                    first_doc = await self.get_document(repo_id, first_result.id)
                except YuqueAPIError:
                    # If we can't read the document, just return search results
                    pass

        return results, first_doc, meta

    # =========================================================================
    # Search Operations
    # =========================================================================

    async def search(
        self,
        query: str,
        search_type: str,
        scope: Optional[str] = None,
        page: int = 1,
    ) -> tuple[list[SearchResult], dict[str, Any]]:
        """Search for documents or repositories.

        Args:
            query: Search keywords (max 200 characters).
            search_type: Search type ('doc' or 'repo').
            scope: Search scope (e.g., 'user_login' or 'user/repo').
            page: Page number (1-100).

        Returns:
            Tuple of (list of SearchResult objects, pagination metadata).

        Raises:
            YuqueAPIError: If the request fails.
        """
        params: dict[str, Any] = {"q": query, "type": search_type, "page": page}
        if scope:
            params["scope"] = scope

        result = await self._request("GET", "/api/v2/search", params=params)

        results = [SearchResult(**item) for item in result.get("data", [])]
        meta = result.get("meta", {})
        return results, meta
