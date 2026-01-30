# Yuque MCP Server

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)

**English | [简体中文](README.md)**

A Model Context Protocol (MCP) server for seamless integration with [Yuque (语雀)](https://www.yuque.com) - enabling AI assistants like Claude to manage your knowledge base through standardized tools.

## Features

### Document Management
- ✅ Create, read, update, and delete documents
- ✅ Support for multiple formats (Markdown, HTML, Lake)
- ✅ List documents with pagination
- ✅ **One-step document creation with TOC** (`create_document_with_toc`)

### Repository Management
- ✅ Get all your knowledge bases in one call (`get_my_repositories`)
- ✅ View repository with full TOC structure (`get_repository_overview`)
- ✅ Create new knowledge bases

### Table of Contents
- ✅ Hierarchical TOC view included with repository overview
- ✅ Add/move/remove documents in TOC
- ✅ Organize content with folders

### Search & Discovery
- ✅ Search and read documents in one call (`search_and_read`)
- ✅ Get current user information

## Installation

### Prerequisites
- Python 3.10 or higher
- A Yuque account with API token

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/EnglandLobster/yuque-mcp.git
   cd yuque-mcp
   ```

2. **Install with pip**
   ```bash
   pip install -e .
   ```

   Or with uv:
   ```bash
   uv venv
   uv pip install -e .
   ```

3. **Configure API token**
   ```bash
   cp .env.example .env
   ```

   Get your API token from: https://www.yuque.com/settings/tokens

   Edit `.env`:
   ```env
   YUQUE_API_TOKEN=your_token_here
   YUQUE_BASE_URL=https://www.yuque.com
   ```

## Usage

### With Claude Code CLI

Add to `~/.claude.json` or project-level `.mcp.json`:

```json
{
  "mcpServers": {
    "yuque": {
      "type": "stdio",
      "command": "/path/to/yuque-mcp/.venv/bin/python",
      "args": ["-m", "yuque_mcp.server"],
      "env": {
        "YUQUE_API_TOKEN": "your_token_here"
      }
    }
  }
}
```

Or add via CLI:
```bash
claude mcp add --scope user --transport stdio \
  --env YUQUE_API_TOKEN=your_token \
  yuque -- python -m yuque_mcp.server
```

### With Claude Desktop

Add to Claude Desktop config:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

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

### Standalone

```bash
# Using the installed script
yuque-mcp

# Or run directly
python -m yuque_mcp.server
```

## Available Tools (11 tools)

### Document Operations (5 tools)

| Tool | Description |
|------|-------------|
| `create_document_with_toc` | Create document and add to TOC in one step (recommended) |
| `get_document` | Retrieve document content and metadata |
| `update_document` | Update document title, content, or settings |
| `delete_document` | Remove a document |
| `list_documents` | List all documents with pagination |

### Repository Operations (3 tools)

| Tool | Description |
|------|-------------|
| `get_my_repositories` | Get current user info + all repositories in one call |
| `get_repository_overview` | Get repository details + TOC structure in one call |
| `create_repository` | Create a new knowledge base |

### TOC Management (1 tool)

| Tool | Description |
|------|-------------|
| `update_toc` | Add, move, or remove TOC items |

### Search & User (2 tools)

| Tool | Description |
|------|-------------|
| `search_and_read` | Search documents and read the first result in one call |
| `get_current_user` | Get authenticated user info |

## Common Workflows

### Creating a Document (Recommended)

Use `create_document_with_toc` for one-step creation:

```
create_document_with_toc(
    repo_id="123",
    title="Getting Started",
    body="# Welcome\n\nYour content here...",
    parent_uuid="folder-uuid"  # optional, adds to root if omitted
)
```

### Creating a Document (Two-step)

If you need more control:

1. Create the document:
   ```
   create_document(repo_id="123", title="My Doc", body="# Content")
   ```

2. Add to TOC:
   ```
   update_toc(repo_id="123", action="appendNode", action_mode="child",
              doc_ids="456", node_type="DOC")
   ```

### Browsing Repository Structure

```
get_toc(repo_id="123")
```

Returns hierarchical structure with folders (📁) and documents (📄).

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `YUQUE_API_TOKEN` | Yes | - | Your Yuque API token |
| `YUQUE_BASE_URL` | No | `https://www.yuque.com` | Yuque API base URL |

### Visibility Levels

| Value | Meaning |
|-------|---------|
| `0` | Private (default) |
| `1` | Public |
| `2` | Internal (organization only) |

### Content Formats

| Format | Description |
|--------|-------------|
| `markdown` | Standard Markdown (default) |
| `html` | HTML format |
| `lake` | Yuque's native rich text format |

## Error Handling

The server provides bilingual error messages (Chinese + English):

| Code | Message |
|------|---------|
| 400 | 请求参数非法 (Invalid request parameters) |
| 401 | Token/Scope 未通过鉴权 (Authentication failed) |
| 403 | 无操作权限 (Permission denied) |
| 404 | 实体未找到 (Entity not found) |
| 422 | 请求参数校验失败 (Validation failed) |
| 429 | 访问频率超限 (Rate limit exceeded) |
| 500 | 内部错误 (Internal server error) |

## Development

### Setup Development Environment

```bash
# Clone and install with dev dependencies
git clone https://github.com/EnglandLobster/yuque-mcp.git
cd yuque-mcp
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
pytest --cov=yuque_mcp  # with coverage
```

### Code Quality

```bash
ruff check .           # linting
ruff format .          # formatting
mypy src/yuque_mcp     # type checking
```

### Project Structure

```
yuque-mcp/
├── src/yuque_mcp/
│   ├── __init__.py    # Package exports
│   ├── server.py      # FastMCP server with 15 tools
│   ├── client.py      # Async Yuque API client
│   └── models.py      # Pydantic models and enums
├── tests/
│   ├── __init__.py
│   ├── conftest.py    # Pytest fixtures
│   └── test_client.py # Client tests
├── .env.example
├── .github/
│   └── workflows/
│       └── ci.yml     # GitHub Actions CI
├── pyproject.toml
├── LICENSE
├── CLAUDE.md          # Instructions for AI assistants
└── README.md
```

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Run linting (`ruff check . && ruff format .`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## API Reference

- Yuque API Documentation: https://www.yuque.com/yuque/developer/api
- MCP Specification: https://modelcontextprotocol.io
- FastMCP Documentation: https://gofastmcp.com

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Yuque (语雀)](https://www.yuque.com) - Knowledge base platform
- [Anthropic](https://anthropic.com) - Model Context Protocol
- [FastMCP](https://gofastmcp.com) - High-level MCP Python SDK
