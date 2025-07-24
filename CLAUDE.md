# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Aptible MCP is a Mission Control Protocol (MCP) integration for interacting with the Aptible API. It provides a standardized way to manage Aptible resources using Pydantic models and consistent CRUD operations.

## Common Commands

### Running the Application

```bash
# Start the MCP server
python main.py
```

### Development Commands

```bash
# Run tests
just test

# Run a single test file
APTIBLE_TOKEN="foobar" APTIBLE_API_ROOT_URL="http://localhost:3000" APTIBLE_AUTH_ROOT_URL="http://localhost:3001" python -m pytest -v -s tests/test_file.py

# Run linting
just lint

# Format code and sort dependencies
just pretty

# Run type checking
just typecheck
```

## Authentication

The application requires an Aptible API token for authentication. The token is sourced in the following order:
1. From the `APTIBLE_TOKEN` environment variable
2. From a local tokens file at `~/.aptible/tokens.json`

When running locally, make sure to either:
- Set the `APTIBLE_TOKEN` environment variable
- Have a valid token in the tokens file (requires logging in with the Aptible CLI first)

## Architecture

### Core Components

1. **MCP Server** (`main.py`)
   - Creates and initializes a FastMCP server
   - Registers tool functions that correspond to API operations
   - Handles the communication protocol

2. **API Client** (`api_client.py`)
   - Manages authentication with the Aptible API
   - Provides methods for making HTTP requests (GET, POST, PUT, DELETE)
   - Handles response parsing and error handling

3. **Resource Models** (`models/`)
   - Base models and resource managers (`models/base.py`)
   - Resource-specific models and operations for:
     - Accounts (`models/account.py`)
     - Apps (`models/app.py`)
     - Databases (`models/database.py`)
     - Stacks (`models/stack.py`)
     - VHosts (`models/vhost.py`)

### Data Flow

1. MCP server receives a command from the client
2. The appropriate tool function is invoked
3. The tool function calls methods on the resource manager
4. The resource manager uses the API client to make requests
5. Responses are parsed into Pydantic models
6. Results are returned to the client

### Key Design Patterns

1. **Resource Base Model**
   - All resource models extend `ResourceBase`
   - Common fields: `id`, `handle`, and `links`
   - Model validator to transform between API's `_links` and Pydantic's `links`

2. **Resource Manager**
   - Generic manager class for CRUD operations
   - Type-parameterized to work with specific resource types
   - Common methods: `list()`, `get()`, `create()`, `delete()`
   - Resource-specific methods for unique operations

3. **Computed Properties**
   - Resource models use `@computed_field` for derived properties
   - Example: `stack_id` in `Account` is extracted from links data

## Important Notes

1. The API uses `_links` for relationships, but Pydantic doesn't allow leading underscores in field names. The codebase handles this transformation in both directions.

2. Resources often reference each other by ID embedded in URL paths (e.g., `/stacks/123`). The code extracts these IDs from the links data.

3. Resource handles (names) are unique within their scope, but some resources (like apps) can have duplicate handles across different accounts. The API provides methods to handle this disambiguation.

4. Asynchronous operations (like provisioning) use a wait_for_operation pattern to ensure completion.