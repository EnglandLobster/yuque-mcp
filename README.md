# Yuque MCP Server

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)

**[English](README_EN.md) | 简体中文**

为 [语雀（Yuque）](https://www.yuque.com) 提供的模型上下文协议（MCP）服务器 - 让 Claude 等 AI 助手能够通过标准化工具管理你的语雀知识库。

## 功能特性

### 文档管理
- ✅ 创建、读取、更新和删除文档
- ✅ 支持多种格式（Markdown、HTML、Lake）
- ✅ 分页列出文档
- ✅ **一步创建文档并添加到目录** (`create_document_with_toc`)

### 知识库管理
- ✅ 一次调用获取所有知识库 (`get_my_repositories`)
- ✅ 查看知识库及完整目录结构 (`get_repository_overview`)
- ✅ 创建新知识库

### 目录管理
- ✅ 知识库概览中包含层级目录视图
- ✅ 在目录中添加/移动/删除文档
- ✅ 使用文件夹组织内容

### 搜索与发现
- ✅ 一次调用搜索并读取文档 (`search_and_read`)
- ✅ 获取当前用户信息

## 安装

### 前置要求
- Python 3.10 或更高版本
- 语雀账号及 API Token

### 快速开始

1. **克隆仓库**
   ```bash
   git clone https://github.com/EnglandLobster/yuque-mcp.git
   cd yuque-mcp
   ```

2. **安装依赖**
   ```bash
   pip install -e .
   ```

   或使用 uv：
   ```bash
   uv venv
   uv pip install -e .
   ```

3. **配置 API Token**
   ```bash
   cp .env.example .env
   ```

   从这里获取你的 API Token：https://www.yuque.com/settings/tokens

   编辑 `.env` 文件：
   ```env
   YUQUE_API_TOKEN=你的token
   YUQUE_BASE_URL=https://www.yuque.com
   ```

## 使用方法

### 与 Claude Code CLI 集成

添加到 `~/.claude.json` 或项目级别的 `.mcp.json`：

```json
{
  "mcpServers": {
    "yuque": {
      "type": "stdio",
      "command": "/path/to/yuque-mcp/.venv/bin/python",
      "args": ["-m", "yuque_mcp.server"],
      "env": {
        "YUQUE_API_TOKEN": "你的token"
      }
    }
  }
}
```

或通过 CLI 添加：
```bash
claude mcp add --scope user --transport stdio \
  --env YUQUE_API_TOKEN=你的token \
  yuque -- python -m yuque_mcp.server
```

### 与 Claude Desktop 集成

添加到 Claude Desktop 配置文件：

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "yuque": {
      "command": "python",
      "args": ["-m", "yuque_mcp.server"],
      "env": {
        "YUQUE_API_TOKEN": "你的token"
      }
    }
  }
}
```

### 独立运行

```bash
# 使用安装的脚本
yuque-mcp

# 或直接运行
python -m yuque_mcp.server
```

## 可用工具（11 个工具）

### 文档操作（5 个工具）

| 工具 | 描述 |
|------|------|
| `create_document_with_toc` | 一步创建文档并添加到目录（推荐） |
| `get_document` | 获取文档内容和元数据 |
| `update_document` | 更新文档标题、内容或设置 |
| `delete_document` | 删除文档 |
| `list_documents` | 分页列出所有文档 |

### 知识库操作（3 个工具）

| 工具 | 描述 |
|------|------|
| `get_my_repositories` | 一次获取当前用户信息和所有知识库 |
| `get_repository_overview` | 一次获取知识库详情和目录结构 |
| `create_repository` | 创建新知识库 |

### 目录管理（1 个工具）

| 工具 | 描述 |
|------|------|
| `update_toc` | 添加、移动或删除目录项 |

### 搜索与用户（2 个工具）

| 工具 | 描述 |
|------|------|
| `search_and_read` | 一次搜索并读取第一个结果 |
| `get_current_user` | 获取认证用户信息 |

## 常见工作流

### 创建文档（推荐方式）

使用 `create_document_with_toc` 一步完成创建：

```python
create_document_with_toc(
    repo_id="123",
    title="快速开始",
    body="# 欢迎\n\n你的内容...",
    parent_uuid="folder-uuid"  # 可选，省略则添加到根目录
)
```

### 创建文档（两步方式）

如果需要更多控制：

1. 创建文档：
   ```python
   create_document(repo_id="123", title="我的文档", body="# 内容")
   ```

2. 添加到目录：
   ```python
   update_toc(repo_id="123", action="appendNode", action_mode="child",
              doc_ids="456", node_type="DOC")
   ```

### 浏览知识库结构

```python
get_toc(repo_id="123")
```

返回带有文件夹（📁）和文档（📄）的层级结构。

## 配置

### 环境变量

| 变量 | 必需 | 默认值 | 描述 |
|------|------|--------|------|
| `YUQUE_API_TOKEN` | 是 | - | 你的语雀 API Token |
| `YUQUE_BASE_URL` | 否 | `https://www.yuque.com` | 语雀 API 基础 URL |

### 可见性级别

| 值 | 含义 |
|----|------|
| `0` | 私密（默认） |
| `1` | 公开 |
| `2` | 内部可见（仅组织成员） |

### 内容格式

| 格式 | 描述 |
|------|------|
| `markdown` | 标准 Markdown（默认） |
| `html` | HTML 格式 |
| `lake` | 语雀原生富文本格式 |

## 错误处理

服务器提供双语错误消息（中文 + 英文）：

| 状态码 | 消息 |
|--------|------|
| 400 | 请求参数非法 (Invalid request parameters) |
| 401 | Token/Scope 未通过鉴权 (Authentication failed) |
| 403 | 无操作权限 (Permission denied) |
| 404 | 实体未找到 (Entity not found) |
| 422 | 请求参数校验失败 (Validation failed) |
| 429 | 访问频率超限 (Rate limit exceeded) |
| 500 | 内部错误 (Internal server error) |

## 开发

### 设置开发环境

```bash
# 克隆并安装开发依赖
git clone https://github.com/EnglandLobster/yuque-mcp.git
cd yuque-mcp
pip install -e ".[dev]"
```

### 运行测试

```bash
pytest
pytest --cov=yuque_mcp  # 带覆盖率报告
```

### 代码质量检查

```bash
ruff check .           # 代码检查
ruff format .          # 代码格式化
mypy src/yuque_mcp     # 类型检查
```

### 项目结构

```
yuque-mcp/
├── src/yuque_mcp/
│   ├── __init__.py    # 包导出
│   ├── server.py      # FastMCP 服务器（11 个工具）
│   ├── client.py      # 异步语雀 API 客户端
│   └── models.py      # Pydantic 模型和枚举
├── tests/
│   ├── __init__.py
│   ├── conftest.py    # Pytest 固件
│   └── test_client.py # 客户端测试
├── .env.example
├── .github/
│   └── workflows/
│       └── ci.yml     # GitHub Actions CI
├── pyproject.toml
├── LICENSE
├── CLAUDE.md          # AI 助手使用说明
└── README.md
```

## 贡献

欢迎贡献！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 进行修改
4. 运行测试 (`pytest`)
5. 运行代码检查 (`ruff check . && ruff format .`)
6. 提交更改 (`git commit -m 'Add amazing feature'`)
7. 推送到分支 (`git push origin feature/amazing-feature`)
8. 开启 Pull Request

## API 参考

- 语雀 API 文档：https://www.yuque.com/yuque/developer/api
- MCP 规范：https://modelcontextprotocol.io
- FastMCP 文档：https://gofastmcp.com

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 致谢

- [语雀（Yuque）](https://www.yuque.com) - 知识库平台
- [Anthropic](https://anthropic.com) - 模型上下文协议
- [FastMCP](https://gofastmcp.com) - 高级 MCP Python SDK
