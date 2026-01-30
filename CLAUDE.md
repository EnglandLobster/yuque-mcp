# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Model Context Protocol (MCP) server that integrates with Yuque API (语雀), enabling AI agents like Claude to manage knowledge bases through MCP-compatible tools.

## Development Commands

### Installation
```bash
# Install package in editable mode
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"
```

### Running the Server

```bash
# Using installed script
yuque-mcp

# Or run directly as module
python -m yuque_mcp.server
```

### Testing
```bash
# Run all tests (note: test suite not yet implemented)
pytest

# Run tests with async support
pytest -v

# Run with coverage
pytest --cov=yuque_mcp
```

### Manual Testing

```bash
# Test server starts correctly
python -m yuque_mcp.server

# Verify configuration loads
python -c "from yuque_mcp.models import YuqueConfig; print(YuqueConfig())"
```

## Architecture

### Three-Layer Design

1. **models.py** - Configuration and data models
   - `YuqueConfig`: Environment-based configuration using pydantic-settings (reads `YUQUE_API_TOKEN` and `YUQUE_BASE_URL`)
   - `YuqueAPIError`: Custom exception with status code, message, and details
   - Pydantic models: `User`, `Book`, `Doc`, `TocItem`, `SearchResult`

2. **client.py** - HTTP API client layer
   - `YuqueClient`: Async httpx-based client with X-Auth-Token authentication
   - Implements all Yuque API v2 endpoints (docs, repos, TOC, search, user)
   - Error handling with Chinese error messages mapped from HTTP status codes

3. **server.py** - FastMCP server with 14 tools
   - Initializes FastMCP instance and YuqueClient
   - Exposes async tool functions decorated with `@mcp.tool()`
   - Returns formatted strings (not raw JSON) for better LLM consumption

### Critical Workflow: Document Creation

Documents created via `create_document` are NOT automatically visible in the repository. You must call `update_toc` separately to add them to the table of contents:

```python
# Step 1: Create document
result = create_document(repo_id=123, title="My Doc", body="# Content")

# Step 2: Add to TOC (REQUIRED)
update_toc(repo_id=123, action='appendNode', action_mode='child',
           doc_ids='456', type='DOC')
```

### MCP Tool Categories

- **Document Operations** (5 tools): create_document, get_document, update_document, delete_document, list_documents
- **Repository Operations** (5 tools): create_repository, get_repository, list_repositories, update_repository, delete_repository
- **TOC Management** (2 tools): get_toc, update_toc
- **Search & User** (2 tools): search_content, get_current_user

## Configuration

Create `.env` file based on `.env.example`:
```env
YUQUE_API_TOKEN=your_token_here
YUQUE_BASE_URL=https://www.yuque.com
```

Get API token from: https://www.yuque.com/settings/tokens

## Integration with MCP Clients

### Claude Desktop (macOS/Windows)

Add to Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "yuque": {
      "command": "python",
      "args": ["-m", "yuque_mcp.server"],
      "env": {
        "YUQUE_API_TOKEN": "your_token_here"
      }
    }
  }
}
```

### Claude Code CLI

For Claude Code CLI, use `~/.claude.json` or `.mcp.json` (project-level):

```json
{
  "mcpServers": {
    "yuque": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "yuque_mcp.server"],
      "env": {
        "YUQUE_API_TOKEN": "your_token_here",
        "YUQUE_BASE_URL": "https://www.yuque.com"
      }
    }
  }
}
```

Or add via CLI command:
```bash
claude mcp add --scope user --transport stdio \
  --env YUQUE_API_TOKEN=your_token \
  yuque -- python -m yuque_mcp.server
```

## Error Handling

The client maps HTTP status codes to Chinese error messages:
- 400: 请求参数非法 (Invalid request parameters)
- 401: Token/Scope 未通过鉴权 (Token authentication failure)
- 403: 无操作权限 (Insufficient permissions)
- 404: 实体未找到 (Entity not found)
- 422: 请求参数校验失败 (Request validation failed)
- 429: 访问频率超限 (Rate limit exceeded)
- 500: 内部错误 (Internal error)

All tool functions catch `YuqueAPIError` and return user-friendly error strings prefixed with `✗ Error:`.

### Client Lifecycle

The `YuqueClient` uses an async `httpx.AsyncClient` that should be properly closed. Currently, the global client instance in `server.py` is not explicitly closed. For production use, consider implementing proper cleanup in an async context manager.
