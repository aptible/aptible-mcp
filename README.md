# Aptible MCP

A Mission Control Protocol (MCP) integration for Aptible.

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

Start the MCP server with:

```bash
python main.py
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
