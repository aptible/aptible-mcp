from mcp.server.fastmcp import FastMCP
from typing import Any, Dict, List, Optional

from api_client import AptibleApiClient
from models import (
    AccountManager,
    App,
    AppManager,
    Database,
    DatabaseManager,
    StackManager,
    VhostManager,
)
from models.service import Service, ServiceManager


mcp = FastMCP("aptible")


api_client = AptibleApiClient()


account_manager = AccountManager(api_client)
app_manager = AppManager(api_client)
database_manager = DatabaseManager(api_client)
stack_manager = StackManager(api_client)
service_manager = ServiceManager(api_client)
vhost_manager = VhostManager(api_client)
app_manager.service_manager = service_manager


@mcp.tool()
async def list_accounts() -> List[Dict[str, Any]]:
    """
    List all accounts/environments.
    """
    accounts = await account_manager.list()
    return [account.model_dump() for account in accounts]


@mcp.tool()
async def get_account(account_handle: str) -> Optional[Dict[str, Any]]:
    """
    Get account/environment by handle.
    """
    account = await account_manager.get(account_handle)
    return account.model_dump() if account else None


@mcp.tool()
async def get_accounts_by_stack(stack_name: str) -> List[Dict[str, Any]]:
    """
    Get all accounts/environments in a stack by stack name.
    """
    stack = await stack_manager.get(stack_name)
    if not stack:
        raise Exception(f"Stack {stack_name} not found.")

    accounts = await account_manager.get_by_stack_id(stack.id)
    return [account.model_dump() for account in accounts]


@mcp.tool()
async def create_account(account_name: str, stack_name: str) -> Dict[str, Any]:
    """
    Create a new account/environment.
    """
    stack = await stack_manager.get(stack_name)
    if not stack:
        raise Exception(f"Stack {stack_name} not found.")
    data = {"handle": account_name, "stack_id": stack.id}
    account = await account_manager.create(data)
    return account.model_dump()


@mcp.tool()
async def list_apps() -> List[Dict[str, Any]]:
    """
    List all apps.
    """
    apps = await app_manager.list()
    return [app.model_dump() for app in apps]


@mcp.tool()
async def get_app(
    app_handle: str, account_handle: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Get app by handle.

    Because app names are only unique within an account/environment,
    an account handle can also be provided.
    """
    apps = await app_manager.list()
    matches = [app for app in apps if app.handle == app_handle]

    if len(matches) == 0:
        raise Exception(f"No app with handle {app_handle}.")

    if len(matches) == 1 and not account_handle:
        return matches[0].model_dump()

    if account_handle:
        account = await account_manager.get(account_handle)
        if not account:
            raise Exception(f"Account {account_handle} not found.")

        account_matches = [app for app in matches if app.account_id == account.id]

        if not account_matches:
            raise Exception(
                f"No app with handle {app_handle} in account {account_handle}."
            )

        return account_matches[0].model_dump()

    raise Exception(
        f"Multiple apps found with handle {app_handle}. Please provide an account handle."
    )


@mcp.tool()
async def create_app(
    app_handle: str, account_handle: str, docker_image: str
) -> Dict[str, Any]:
    """
    Create a new app.
    """
    account = await account_manager.get(account_handle)
    if not account:
        raise Exception(f"Account {account_handle} not found.")
    data = {
        "handle": app_handle,
        "account_id": account.id,
        "docker_image": docker_image,
    }
    app = await app_manager.create(data)
    return app.model_dump()


@mcp.tool()
async def configure_app(
    app_handle: str, account_handle: Optional[str], env: Dict[str, str]
) -> None:
    """
    Configure app environment variables.
    """
    app_data = await get_app(app_handle, account_handle)
    if not app_data:
        raise Exception(f"App {app_handle} not found.")

    app = App.model_validate(app_data)
    await app_manager.configure(app.id, env)


@mcp.tool()
async def delete_app(app_handle: str, account_handle: Optional[str] = None) -> None:
    """
    Delete an app.
    """
    app_data = await get_app(app_handle, account_handle)
    if not app_data:
        raise Exception(f"App {app_handle} not found.")

    app = App.model_validate(app_data)
    await app_manager.delete(app.id)


@mcp.tool()
async def list_available_database_types() -> List[Dict[str, Any]]:
    """
    List all available database types. When creating a database,
    the image id provided via this method is needed.
    """
    db_types = await database_manager.list_available_types()
    return [db_type.model_dump() for db_type in db_types]


@mcp.tool()
async def list_databases() -> List[Dict[str, Any]]:
    """
    List all databases.
    """
    databases = await database_manager.list()
    return [db.model_dump() for db in databases]


@mcp.tool()
async def get_database(
    database_handle: str, account_handle: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Get database by handle and optionally account handle.
    """
    databases = await database_manager.list()
    matches = [db for db in databases if db.handle == database_handle]

    if len(matches) == 0:
        raise Exception(f"No database with handle {database_handle}.")

    if len(matches) == 1 and not account_handle:
        return matches[0].model_dump()

    if account_handle:
        account = await account_manager.get(account_handle)
        if not account:
            raise Exception(f"Account {account_handle} not found.")

        account_matches = [db for db in matches if db.account_id == account.id]

        if not account_matches:
            raise Exception(
                f"No database with handle {database_handle} in account {account_handle}."
            )

        return account_matches[0].model_dump()

    raise Exception(
        f"Multiple databases found with handle {database_handle}. Please provide an account handle."
    )


@mcp.tool()
async def create_database(
    database_handle: str, account_handle: str, image_id: int
) -> Dict[str, Any]:
    """
    Create a new database.
    The image_id should be the ID found via list_available_database_types.
    """
    account = await account_manager.get(account_handle)
    if not account:
        raise Exception(f"Account {account_handle} not found.")

    data = {
        "handle": database_handle,
        "account_id": account.id,
        "image_id": image_id,
    }
    database = await database_manager.create(data)
    return database.model_dump()


@mcp.tool()
async def delete_database(
    database_handle: str, account_handle: Optional[str] = None
) -> None:
    """
    Delete a database.
    """
    database_data = await get_database(database_handle, account_handle)
    if not database_data:
        raise Exception(f"Database {database_handle} not found.")

    database = Database.model_validate(database_data)
    await database_manager.delete(database.id)


@mcp.tool()
async def list_stacks() -> List[Dict[str, Any]]:
    """
    List all stacks.
    """
    stacks = await stack_manager.list()
    return [stack.model_dump() for stack in stacks]


@mcp.tool()
async def get_stack(stack_name: str) -> Optional[Dict[str, Any]]:
    """
    Get stack by name.
    """
    stack = await stack_manager.get(stack_name)
    return stack.model_dump() if stack else None


@mcp.tool()
async def list_vhosts() -> List[Dict[str, Any]]:
    """
    List all vhosts/endpoints).
    """
    vhosts = await vhost_manager.list()
    return [vhost.model_dump() for vhost in vhosts]


@mcp.tool()
async def get_vhost(vhost_id: str) -> Optional[Dict[str, Any]]:
    """
    Get vhost by ID.
    """
    vhost = await vhost_manager.get(vhost_id)
    return vhost.model_dump() if vhost else None


@mcp.tool()
async def create_vhost(
    app_handle: str, service_handle: str, account_handle: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new vhost/endpoint for a Service.

    Service handle is a bit weird, since it's auto-assigned by Aptible
    and not set by the user. The user assigns with process_type in the procfile.
    Since this is being used by AI, that shouldn't matter, though.

    TODO: Add support for database endpoints and custom endpoints.
          Currently, since there's no tools for handling DNS, we only
          support creating the default on-aptible.com domains for Services.
    """
    app_data = await get_app(app_handle, account_handle)
    if not app_data:
        raise Exception(f"App {app_handle} not found.")

    app = App.model_validate(app_data)

    services = await service_manager.list_by_app(app.id)
    service_matches = [s for s in services if s.handle == service_handle]

    if not service_matches:
        raise Exception(
            f"No service with handle {service_handle} found in app {app_handle}."
        )

    service = service_matches[0]
    vhost = await vhost_manager.create({"service_id": service.id})
    return vhost.model_dump()


@mcp.tool()
async def delete_vhost(vhost_id: int) -> None:
    """
    Delete a vhost/endpoint.
    """
    await vhost_manager.delete_vhost(vhost_id)


@mcp.tool()
async def list_services(
    app_handle: str, account_handle: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    List all services for a specific app.
    """
    app_data = await get_app(app_handle, account_handle)
    if not app_data:
        raise Exception(f"App {app_handle} not found.")

    app = App.model_validate(app_data)
    services = await service_manager.list_by_app(app.id)
    return [service.model_dump() for service in services]


@mcp.tool()
async def get_service(
    app_handle: str, service_handle: str, account_handle: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get a service by handle within a specific app.
    """
    app_data = await get_app(app_handle, account_handle)
    if not app_data:
        raise Exception(f"App {app_handle} not found.")

    app = App.model_validate(app_data)
    service = await service_manager.get_by_handle_and_app(service_handle, app.id)

    if not service:
        raise Exception(
            f"No service with handle {service_handle} found in app {app_handle}."
        )

    return service.model_dump()


@mcp.tool()
async def scale_service(
    app_handle: str,
    service_handle: str,
    container_count: Optional[int] = None,
    container_memory_limit_mb: Optional[int] = None,
    account_handle: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Scale a service by changing container count or size.
    """
    if container_count is None and container_memory_limit_mb is None:
        raise ValueError(
            "Must specify at least one of container_count or container_size"
        )

    service_data = await get_service(app_handle, service_handle, account_handle)
    service = Service.model_validate(service_data)

    updated_service = await service_manager.scale(
        service.id, container_count, container_memory_limit_mb
    )
    return updated_service.model_dump()


@mcp.tool()
async def list_service_vhosts(
    app_handle: str, service_handle: str, account_handle: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    List all vhosts for a specific service.
    """
    service_data = await get_service(app_handle, service_handle, account_handle)
    service = Service.model_validate(service_data)

    vhosts = await vhost_manager.list_by_service(service.id)
    return [vhost.model_dump() for vhost in vhosts]


if __name__ == "__main__":
    mcp.run(transport="stdio")
