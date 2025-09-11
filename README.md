# Aptible MCP

An MCP server for [Aptible](https://www.aptible.com).

> [!NOTE]
> This MCP server is still under development.

## Overview

This project provides MCP tools for interacting with the Aptible API. It uses Pydantic models for standardized data handling and provides consistent CRUD operations for Aptible resources.

## Features

- Standardized models for Aptible resources (Account, App, Database, etc.)
- Consistent CRUD operations across resource types
- Pydantic validation for request/response data
- Type hints for better developer experience

## Structure

- `api_client.py` - API client for interacting with the Aptible API
- `models/` - Pydantic models for Aptible resources
  - `base.py` - Base models and resource manager
  - Resource-specific models (account.py, app.py, etc.)
- `main.py` - MCP tools implementation

## Usage

This MCP server assumes you are currently logged in via the [Aptible CLI](https://www.aptible.com/docs/reference/aptible-cli/overview).

Once logged in, start the MCP server with:

```bash
uv run python main.py
```

Or add the MCP server to your client config:

```json
{
  "mcpServers": {
    "aptible": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/the/mcp/server",
        "run",
        "main.py"
      ]
    }
  }
}
```

## Testing

To run tests + linting

```bash
just test

just typecheck

just lint
```


## Resource Models

All resource models extend the base `ResourceBase` class and include:
- `id` - Unique identifier
- `handle` - Human-readable identifier
- Additional resource-specific fields

## Resource Managers

Each resource type has a dedicated manager class that extends `ResourceManager` and provides:
- `list()` - List all resources
- `get(identifier)` - Get a specific resource
- `create(data)` - Create a new resource
- Resource-specific operations
