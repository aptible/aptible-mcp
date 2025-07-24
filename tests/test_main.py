import pytest
from unittest.mock import AsyncMock, Mock, patch

from models.app import App
from models.account import Account
from models.database import Database
from models.service import Service
from models.stack import Stack
from models.database import DatabaseImage
from models.vhost import Vhost
from main import (
    list_accounts,
    get_account,
    get_accounts_by_stack,
    create_account,
    list_stacks,
    get_stack,
    list_apps,
    get_app,
    create_app,
    configure_app,
    delete_app,
    list_available_database_types,
    list_databases,
    get_database,
    create_database,
    delete_database,
    list_vhosts,
    get_vhost,
    create_vhost,
    delete_vhost,
    list_services,
    get_service,
    scale_service,
    list_service_vhosts,
)


@pytest.fixture
def mock_account_manager():
    """
    Fixture providing a mock AccountManager.
    """
    with patch("main.account_manager") as mock_manager:
        yield mock_manager


@pytest.fixture
def mock_stack_manager():
    """
    Fixture providing a mock StackManager.
    """
    with patch("main.stack_manager") as mock_manager:
        yield mock_manager


@pytest.fixture
def mock_app_manager():
    """
    Fixture providing a mock AppManager.
    """
    with patch("main.app_manager") as mock_manager:
        yield mock_manager


@pytest.fixture
def mock_database_manager():
    """
    Fixture providing a mock DatabaseManager.
    """
    with patch("main.database_manager") as mock_manager:
        yield mock_manager


@pytest.fixture
def mock_vhost_manager():
    """
    Fixture providing a mock VhostManager.
    """
    with patch("main.vhost_manager") as mock_manager:
        yield mock_manager


@pytest.fixture
def mock_service_manager():
    """
    Fixture providing a mock ServiceManager.
    """
    with patch("main.service_manager") as mock_manager:
        yield mock_manager


@pytest.mark.asyncio
async def test_list_accounts(mock_account_manager):
    """
    Test that list_accounts correctly returns account data.
    """
    mock_accounts = [
        Account(
            id=1,
            handle="test-account-1",
            created_at="2023-01-01T12:00:00Z",
            updated_at="2023-01-01T12:00:00Z",
            links={"stack": {"href": "https://api.aptible.com/stacks/123"}},
        ),
        Account(
            id=2,
            handle="test-account-2",
            created_at="2023-01-02T12:00:00Z",
            updated_at="2023-01-02T12:00:00Z",
            links={"stack": {"href": "https://api.aptible.com/stacks/456"}},
        ),
    ]
    mock_account_manager.list = AsyncMock(return_value=mock_accounts)

    result = await list_accounts()
    mock_account_manager.list.assert_called_once()
    assert len(result) == 2
    assert result[0]["id"] == 1
    assert result[0]["handle"] == "test-account-1"
    assert result[0]["stack_id"] == 123
    assert result[1]["id"] == 2
    assert result[1]["handle"] == "test-account-2"
    assert result[1]["stack_id"] == 456


@pytest.mark.asyncio
async def test_get_account_success(mock_account_manager):
    """
    Test get_account successfully retrieves an account by handle.
    """
    mock_account = Account(
        id=1,
        handle="test-account",
        created_at="2023-01-01T12:00:00Z",
        updated_at="2023-01-01T12:00:00Z",
        links={"stack": {"href": "https://api.aptible.com/stacks/123"}},
    )
    mock_account_manager.get = AsyncMock(return_value=mock_account)

    result = await get_account("test-account")
    mock_account_manager.get.assert_called_once_with("test-account")
    assert result["id"] == 1
    assert result["handle"] == "test-account"
    assert result["stack_id"] == 123


@pytest.mark.asyncio
async def test_get_account_not_found(mock_account_manager):
    """
    Test get_account returns None when account is not found.
    """
    mock_account_manager.get = AsyncMock(return_value=None)

    result = await get_account("nonexistent-account")
    mock_account_manager.get.assert_called_once_with("nonexistent-account")
    assert result is None


@pytest.mark.asyncio
async def test_get_accounts_by_stack_success(mock_stack_manager, mock_account_manager):
    """
    Test get_accounts_by_stack successfully retrieves accounts for a stack.
    """
    mock_stack = Stack(
        id=123,
        name="test-stack",
        region="us-east-1",
        public=False,
        created_at="2023-01-01T12:00:00Z",
        updated_at="2023-01-01T12:00:00Z",
        organization_id="org-123",
    )
    mock_stack_manager.get = AsyncMock(return_value=mock_stack)

    mock_accounts = [
        Account(
            id=1,
            handle="test-account-1",
            created_at="2023-01-01T12:00:00Z",
            updated_at="2023-01-01T12:00:00Z",
            links={"stack": {"href": "https://api.aptible.com/stacks/123"}},
        ),
        Account(
            id=2,
            handle="test-account-2",
            created_at="2023-01-01T12:00:00Z",
            updated_at="2023-01-01T12:00:00Z",
            links={"stack": {"href": "https://api.aptible.com/stacks/123"}},
        ),
    ]
    mock_account_manager.get_by_stack_id = AsyncMock(return_value=mock_accounts)

    result = await get_accounts_by_stack("test-stack")

    mock_stack_manager.get.assert_called_once_with("test-stack")
    mock_account_manager.get_by_stack_id.assert_called_once_with(123)

    assert len(result) == 2
    assert result[0]["id"] == 1
    assert result[0]["handle"] == "test-account-1"
    assert result[1]["id"] == 2
    assert result[1]["handle"] == "test-account-2"


@pytest.mark.asyncio
async def test_get_accounts_by_stack_not_found(mock_stack_manager):
    """
    Test get_accounts_by_stack raises an exception when stack is not found.
    """
    mock_stack_manager.get = AsyncMock(return_value=None)

    with pytest.raises(Exception) as excinfo:
        await get_accounts_by_stack("nonexistent-stack")

    mock_stack_manager.get.assert_called_once_with("nonexistent-stack")
    assert "Stack nonexistent-stack not found" in str(excinfo.value)


@pytest.mark.asyncio
async def test_create_account_success(mock_stack_manager, mock_account_manager):
    """
    Test create_account successfully creates a new account.
    """
    mock_stack = Stack(
        id=123,
        name="test-stack",
        region="us-east-1",
        public=False,
        created_at="2023-01-01T12:00:00Z",
        updated_at="2023-01-01T12:00:00Z",
        organization_id="org-123",
    )
    mock_stack_manager.get = AsyncMock(return_value=mock_stack)

    mock_account = Account(
        id=42,
        handle="new-account",
        created_at="2023-01-01T12:00:00Z",
        updated_at="2023-01-01T12:00:00Z",
        links={"stack": {"href": "https://api.aptible.com/stacks/123"}},
    )
    mock_account_manager.create = AsyncMock(return_value=mock_account)

    result = await create_account("new-account", "test-stack")

    mock_stack_manager.get.assert_called_once_with("test-stack")
    mock_account_manager.create.assert_called_once_with(
        {"account_name": "new-account", "stack_id": 123}
    )
    assert result["id"] == 42
    assert result["handle"] == "new-account"
    assert result["stack_id"] == 123


@pytest.mark.asyncio
async def test_create_account_stack_not_found(mock_stack_manager):
    """
    Test create_account raises an exception when stack is not found.
    """
    mock_stack_manager.get = AsyncMock(return_value=None)

    with pytest.raises(Exception) as excinfo:
        await create_account("new-account", "nonexistent-stack")

    mock_stack_manager.get.assert_called_once_with("nonexistent-stack")
    assert "Stack nonexistent-stack not found" in str(excinfo.value)


@pytest.mark.asyncio
async def test_list_stacks(mock_stack_manager):
    """
    Test that list_stacks correctly returns stack data.
    """
    mock_stacks = [
        Stack(
            id=123,
            name="test-stack-1",
            region="us-east-1",
            public=False,
            created_at="2023-01-01T12:00:00Z",
            updated_at="2023-01-01T12:00:00Z",
            organization_id="org-123",
        ),
        Stack(
            id=456,
            name="test-stack-2",
            region="us-west-1",
            public=True,
            created_at="2023-01-02T12:00:00Z",
            updated_at="2023-01-02T12:00:00Z",
            organization_id="org-456",
        ),
    ]
    mock_stack_manager.list = AsyncMock(return_value=mock_stacks)

    result = await list_stacks()

    mock_stack_manager.list.assert_called_once()
    assert len(result) == 2
    assert result[0]["id"] == 123
    assert result[0]["name"] == "test-stack-1"
    assert result[0]["region"] == "us-east-1"
    assert result[1]["id"] == 456
    assert result[1]["name"] == "test-stack-2"
    assert result[1]["public"] is True


@pytest.mark.asyncio
async def test_get_stack_success(mock_stack_manager):
    """
    Test get_stack successfully retrieves a stack by name.
    """
    mock_stack = Stack(
        id=123,
        name="test-stack",
        region="us-east-1",
        public=False,
        created_at="2023-01-01T12:00:00Z",
        updated_at="2023-01-01T12:00:00Z",
        organization_id="org-123",
    )
    mock_stack_manager.get = AsyncMock(return_value=mock_stack)

    result = await get_stack("test-stack")

    mock_stack_manager.get.assert_called_once_with("test-stack")
    assert result["id"] == 123
    assert result["name"] == "test-stack"
    assert result["region"] == "us-east-1"


@pytest.mark.asyncio
async def test_get_stack_not_found(mock_stack_manager):
    """
    Test get_stack returns None when stack is not found.
    """
    mock_stack_manager.get = AsyncMock(return_value=None)

    result = await get_stack("nonexistent-stack")

    mock_stack_manager.get.assert_called_once_with("nonexistent-stack")
    assert result is None


@pytest.mark.asyncio
async def test_list_apps(mock_app_manager):
    """
    Test that list_apps correctly returns app data.
    """
    mock_apps = [
        App(
            id=1,
            handle="test-app-1",
            created_at="2023-01-01T12:00:00Z",
            updated_at="2023-01-01T12:00:00Z",
            status="provisioned",
            links={"account": {"href": "https://api.aptible.com/accounts/123"}},
        ),
        App(
            id=2,
            handle="test-app-2",
            created_at="2023-01-02T12:00:00Z",
            updated_at="2023-01-02T12:00:00Z",
            status="provisioning",
            links={"account": {"href": "https://api.aptible.com/accounts/456"}},
        ),
    ]
    mock_app_manager.list = AsyncMock(return_value=mock_apps)

    result = await list_apps()

    mock_app_manager.list.assert_called_once()
    assert len(result) == 2
    assert result[0]["id"] == 1
    assert result[0]["handle"] == "test-app-1"
    assert result[0]["status"] == "provisioned"
    assert result[1]["id"] == 2
    assert result[1]["handle"] == "test-app-2"


@pytest.mark.asyncio
async def test_get_app_single_match(mock_app_manager):
    """
    Test get_app with a single matching app.
    """
    mock_apps = [
        App(
            id=1,
            handle="test-app",
            created_at="2023-01-01T12:00:00Z",
            updated_at="2023-01-01T12:00:00Z",
            status="provisioned",
            links={"account": {"href": "https://api.aptible.com/accounts/123"}},
        )
    ]
    mock_app_manager.list = AsyncMock(return_value=mock_apps)

    result = await get_app("test-app")

    mock_app_manager.list.assert_called_once()
    assert result["id"] == 1
    assert result["handle"] == "test-app"
    assert result["status"] == "provisioned"


@pytest.mark.asyncio
async def test_get_app_with_account(mock_app_manager, mock_account_manager):
    """
    Test get_app with multiple apps and an account handle.
    """
    mock_apps = [
        App(
            id=1,
            handle="test-app",
            created_at="2023-01-01T12:00:00Z",
            updated_at="2023-01-01T12:00:00Z",
            status="provisioned",
            links={"account": {"href": "https://api.aptible.com/accounts/123"}},
        ),
        App(
            id=2,
            handle="test-app",
            created_at="2023-01-02T12:00:00Z",
            updated_at="2023-01-02T12:00:00Z",
            status="provisioning",
            links={"account": {"href": "https://api.aptible.com/accounts/456"}},
        ),
    ]
    mock_app_manager.list = AsyncMock(return_value=mock_apps)

    mock_account = Account(
        id=123,
        handle="test-account",
        created_at="2023-01-01T12:00:00Z",
        updated_at="2023-01-01T12:00:00Z",
        links={"stack": {"href": "https://api.aptible.com/stacks/789"}},
    )
    mock_account_manager.get = AsyncMock(return_value=mock_account)

    result = await get_app("test-app", "test-account")

    mock_app_manager.list.assert_called_once()
    mock_account_manager.get.assert_called_once_with("test-account")
    assert result["id"] == 1
    assert result["handle"] == "test-app"


@pytest.mark.asyncio
async def test_get_app_no_match(mock_app_manager):
    """
    Test get_app with no matching app.
    """
    mock_app_manager.list = AsyncMock(return_value=[])

    with pytest.raises(Exception) as excinfo:
        await get_app("nonexistent-app")

    mock_app_manager.list.assert_called_once()
    assert "No app with handle nonexistent-app" in str(excinfo.value)


@pytest.mark.asyncio
async def test_get_app_multiple_matches_no_account(mock_app_manager):
    """
    Test get_app with multiple matches but no account provided.
    """
    mock_apps = [
        App(
            id=1,
            handle="test-app",
            created_at="2023-01-01T12:00:00Z",
            updated_at="2023-01-01T12:00:00Z",
            status="provisioned",
            links={"account": {"href": "https://api.aptible.com/accounts/123"}},
        ),
        App(
            id=2,
            handle="test-app",
            created_at="2023-01-02T12:00:00Z",
            updated_at="2023-01-02T12:00:00Z",
            status="provisioning",
            links={"account": {"href": "https://api.aptible.com/accounts/456"}},
        ),
    ]
    mock_app_manager.list = AsyncMock(return_value=mock_apps)

    with pytest.raises(Exception) as excinfo:
        await get_app("test-app")

    mock_app_manager.list.assert_called_once()
    assert "Multiple apps found with handle test-app" in str(excinfo.value)


@pytest.mark.asyncio
async def test_create_app_success(mock_app_manager, mock_account_manager):
    """
    Test create_app successfully creates a new app.
    """
    mock_account = Account(
        id=123,
        handle="test-account",
        created_at="2023-01-01T12:00:00Z",
        updated_at="2023-01-01T12:00:00Z",
        links={"stack": {"href": "https://api.aptible.com/stacks/789"}},
    )
    mock_account_manager.get = AsyncMock(return_value=mock_account)

    mock_app = App(
        id=1,
        handle="new-app",
        created_at="2023-01-01T12:00:00Z",
        updated_at="2023-01-01T12:00:00Z",
        status="provisioning",
        links={"account": {"href": "https://api.aptible.com/accounts/123"}},
    )
    mock_app_manager.create = AsyncMock(return_value=mock_app)

    result = await create_app("new-app", "test-account", "example/image:latest")
    mock_account_manager.get.assert_called_once_with("test-account")
    mock_app_manager.create.assert_called_once_with(
        {
            "app_handle": "new-app",
            "account_id": 123,
            "docker_image": "example/image:latest",
        }
    )
    assert result["id"] == 1
    assert result["handle"] == "new-app"
    assert result["status"] == "provisioning"


@pytest.mark.asyncio
async def test_create_app_account_not_found(mock_account_manager):
    """
    Test create_app raises an exception when account is not found.
    """
    mock_account_manager.get = AsyncMock(return_value=None)

    with pytest.raises(Exception) as excinfo:
        await create_app("new-app", "nonexistent-account", "example/image:latest")

    mock_account_manager.get.assert_called_once_with("nonexistent-account")
    assert "Account nonexistent-account not found" in str(excinfo.value)


@pytest.mark.asyncio
async def test_configure_app_success(mock_app_manager):
    """
    Test configure_app successfully sets environment variables.
    """
    mock_app_data = {
        "id": 1,
        "handle": "test-app",
        "status": "provisioned",
        "created_at": "2023-01-01T12:00:00Z",
        "updated_at": "2023-01-01T12:00:00Z",
        "links": {"account": {"href": "https://api.aptible.com/accounts/123"}},
    }

    mock_app_manager.configure = AsyncMock()

    with patch("main.get_app", new=AsyncMock(return_value=mock_app_data)):
        env_vars = {
            "DATABASE_URL": "postgres://user:pass@host:5432/db",
            "API_KEY": "secret-key",
        }
        await configure_app("test-app", "test-account", env_vars)
        mock_app_manager.configure.assert_called_once_with(1, env_vars)


@pytest.mark.asyncio
async def test_configure_app_not_found():
    """
    Test configure_app raises an exception when app is not found.
    """
    with patch("main.get_app", new=AsyncMock(return_value=None)):
        with pytest.raises(Exception) as excinfo:
            await configure_app("nonexistent-app", "test-account", {"KEY": "VALUE"})

        assert "App nonexistent-app not found" in str(excinfo.value)


@pytest.mark.asyncio
async def test_delete_app_success(mock_app_manager):
    """
    Test delete_app successfully deletes an app.
    """
    mock_app_data = {
        "id": 1,
        "handle": "test-app",
        "status": "provisioned",
        "created_at": "2023-01-01T12:00:00Z",
        "updated_at": "2023-01-01T12:00:00Z",
        "links": {"account": {"href": "https://api.aptible.com/accounts/123"}},
    }

    mock_app_manager.delete = AsyncMock()
    with patch("main.get_app", new=AsyncMock(return_value=mock_app_data)):
        with patch("main.App.account_id", return_value=123):
            await delete_app("test-app")
            mock_app_manager.delete.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_delete_app_not_found():
    """
    Test delete_app raises an exception when app is not found.
    """
    with patch("main.get_app", new=AsyncMock(return_value=None)):
        with pytest.raises(Exception) as excinfo:
            await delete_app("nonexistent-app", "test-account")
        assert "App nonexistent-app not found" in str(excinfo.value)


@pytest.mark.asyncio
async def test_list_available_database_types(mock_database_manager):
    """
    Test list_available_database_types correctly returns database type data.
    """
    mock_db_types = [
        DatabaseImage(
            id=1,
            name="PostgreSQL",
            version="14",
            docker_repo="aptible/postgresql",
            docker_ref="14",
            type="postgresql",
            description="PostgreSQL database",
            default=True,
            created_at="2023-01-01T12:00:00Z",
            updated_at="2023-01-01T12:00:00Z",
            links={},
        ),
        DatabaseImage(
            id=2,
            name="MongoDB",
            version="6.0",
            docker_repo="aptible/mongodb",
            docker_ref="6.0",
            type="mongodb",
            description="MongoDB database",
            default=False,
            created_at="2023-01-01T12:00:00Z",
            updated_at="2023-01-01T12:00:00Z",
            links={},
        ),
    ]
    mock_database_manager.list_available_types = AsyncMock(return_value=mock_db_types)

    result = await list_available_database_types()

    mock_database_manager.list_available_types.assert_called_once()
    assert len(result) == 2
    assert result[0]["id"] == 1
    assert result[0]["name"] == "PostgreSQL"
    assert result[0]["version"] == "14"
    assert result[0]["default"] is True
    assert result[1]["id"] == 2
    assert result[1]["name"] == "MongoDB"


@pytest.mark.asyncio
async def test_list_databases(mock_database_manager):
    """
    Test list_databases correctly returns database data.
    """
    mock_databases = [
        Database(
            id=1,
            handle="test-db-1",
            created_at="2023-01-01T12:00:00Z",
            updated_at="2023-01-01T12:00:00Z",
            status="provisioned",
            type="postgresql",
            links={
                "account": {"href": "https://api.aptible.com/accounts/123"},
                "database_image": {"href": "https://api.aptible.com/database_images/1"},
            },
        ),
        Database(
            id=2,
            handle="test-db-2",
            created_at="2023-01-02T12:00:00Z",
            updated_at="2023-01-02T12:00:00Z",
            status="provisioning",
            type="mongodb",
            links={
                "account": {"href": "https://api.aptible.com/accounts/456"},
                "database_image": {"href": "https://api.aptible.com/database_images/2"},
            },
        ),
    ]
    mock_database_manager.list = AsyncMock(return_value=mock_databases)

    result = await list_databases()

    mock_database_manager.list.assert_called_once()
    assert len(result) == 2
    assert result[0]["id"] == 1
    assert result[0]["handle"] == "test-db-1"
    assert result[0]["status"] == "provisioned"
    assert result[1]["id"] == 2
    assert result[1]["handle"] == "test-db-2"


@pytest.mark.asyncio
async def test_get_database_single_match(mock_database_manager):
    """
    Test get_database with a single matching database.
    """
    mock_databases = [
        Database(
            id=1,
            handle="test-db",
            created_at="2023-01-01T12:00:00Z",
            updated_at="2023-01-01T12:00:00Z",
            status="provisioned",
            type="postgresql",
            links={
                "account": {"href": "https://api.aptible.com/accounts/123"},
                "database_image": {"href": "https://api.aptible.com/database_images/1"},
            },
        )
    ]
    mock_database_manager.list = AsyncMock(return_value=mock_databases)

    result = await get_database("test-db")

    mock_database_manager.list.assert_called_once()
    assert result["id"] == 1
    assert result["handle"] == "test-db"
    assert result["status"] == "provisioned"


@pytest.mark.asyncio
async def test_get_database_with_account(mock_database_manager, mock_account_manager):
    """
    Test get_database with multiple databases and an account handle.
    """
    mock_databases = [
        Database(
            id=1,
            handle="test-db",
            created_at="2023-01-01T12:00:00Z",
            updated_at="2023-01-01T12:00:00Z",
            status="provisioned",
            type="postgresql",
            links={
                "account": {"href": "https://api.aptible.com/accounts/123"},
                "database_image": {"href": "https://api.aptible.com/database_images/1"},
            },
        ),
        Database(
            id=2,
            handle="test-db",
            created_at="2023-01-02T12:00:00Z",
            updated_at="2023-01-02T12:00:00Z",
            status="provisioning",
            type="mongodb",
            links={
                "account": {"href": "https://api.aptible.com/accounts/456"},
                "database_image": {"href": "https://api.aptible.com/database_images/2"},
            },
        ),
    ]
    mock_database_manager.list = AsyncMock(return_value=mock_databases)

    mock_account = Account(
        id=123,
        handle="test-account",
        created_at="2023-01-01T12:00:00Z",
        updated_at="2023-01-01T12:00:00Z",
        links={"stack": {"href": "https://api.aptible.com/stacks/789"}},
    )
    mock_account_manager.get = AsyncMock(return_value=mock_account)

    result = await get_database("test-db", "test-account")

    mock_database_manager.list.assert_called_once()
    mock_account_manager.get.assert_called_once_with("test-account")
    assert result["id"] == 1
    assert result["handle"] == "test-db"


@pytest.mark.asyncio
async def test_get_database_no_match(mock_database_manager):
    """
    Test get_database with no matching database.
    """
    mock_database_manager.list = AsyncMock(return_value=[])

    with pytest.raises(Exception) as excinfo:
        await get_database("nonexistent-db")

    mock_database_manager.list.assert_called_once()
    assert "No database with handle nonexistent-db" in str(excinfo.value)


@pytest.mark.asyncio
async def test_get_database_multiple_matches_no_account(mock_database_manager):
    """
    Test get_database with multiple matches but no account provided.
    """
    mock_databases = [
        Database(
            id=1,
            handle="test-db",
            created_at="2023-01-01T12:00:00Z",
            updated_at="2023-01-01T12:00:00Z",
            status="provisioned",
            type="postgresql",
            links={
                "account": {"href": "https://api.aptible.com/accounts/123"},
                "database_image": {"href": "https://api.aptible.com/database_images/1"},
            },
        ),
        Database(
            id=2,
            handle="test-db",
            created_at="2023-01-02T12:00:00Z",
            updated_at="2023-01-02T12:00:00Z",
            status="provisioning",
            type="mongodb",
            links={
                "account": {"href": "https://api.aptible.com/accounts/456"},
                "database_image": {"href": "https://api.aptible.com/database_images/2"},
            },
        ),
    ]
    mock_database_manager.list = AsyncMock(return_value=mock_databases)

    with pytest.raises(Exception) as excinfo:
        await get_database("test-db")

    mock_database_manager.list.assert_called_once()
    assert "Multiple databases found with handle test-db" in str(excinfo.value)


@pytest.mark.asyncio
async def test_create_database_success(mock_database_manager, mock_account_manager):
    """
    Test create_database successfully creates a new database.
    """

    mock_account = Account(
        id=123,
        handle="test-account",
        created_at="2023-01-01T12:00:00Z",
        updated_at="2023-01-01T12:00:00Z",
        links={"stack": {"href": "https://api.aptible.com/stacks/789"}},
    )
    mock_account_manager.get = AsyncMock(return_value=mock_account)

    mock_database = Database(
        id=1,
        handle="new-db",
        created_at="2023-01-01T12:00:00Z",
        updated_at="2023-01-01T12:00:00Z",
        status="provisioning",
        type="postgresql",
        links={
            "account": {"href": "https://api.aptible.com/accounts/123"},
            "database_image": {"href": "https://api.aptible.com/database_images/42"},
        },
    )
    mock_database_manager.create = AsyncMock(return_value=mock_database)

    result = await create_database("new-db", "test-account", 42)
    mock_account_manager.get.assert_called_once_with("test-account")
    mock_database_manager.create.assert_called_once_with(
        {
            "database_handle": "new-db",
            "account_id": 123,
            "image_id": 42,
        }
    )
    assert result["id"] == 1
    assert result["handle"] == "new-db"
    assert result["status"] == "provisioning"


@pytest.mark.asyncio
async def test_create_database_account_not_found(mock_account_manager):
    """
    Test create_database raises an exception when account is not found.
    """
    mock_account_manager.get = AsyncMock(return_value=None)

    with pytest.raises(Exception) as excinfo:
        await create_database("new-db", "nonexistent-account", 42)

    mock_account_manager.get.assert_called_once_with("nonexistent-account")
    assert "Account nonexistent-account not found" in str(excinfo.value)


@pytest.mark.asyncio
async def test_delete_database_success(mock_database_manager):
    """
    Test delete_database successfully deletes a database.
    """
    mock_database_data = {
        "id": 1,
        "handle": "test-db",
        "status": "provisioned",
        "type": "postgresql",
        "created_at": "2023-01-01T12:00:00Z",
        "updated_at": "2023-01-01T12:00:00Z",
        "links": {
            "account": {"href": "https://api.aptible.com/accounts/123"},
            "database_image": {"href": "https://api.aptible.com/database_images/1"},
        },
    }
    # Use AsyncMock for the delete method to make it awaitable
    mock_database_manager.delete = AsyncMock()

    with patch("main.get_database", new=AsyncMock(return_value=mock_database_data)):
        with patch("main.Database.account_id", return_value=123):
            await delete_database("test-db", "test-account")
            mock_database_manager.delete.assert_called_once_with(
                mock_database_data["id"]
            )


@pytest.mark.asyncio
async def test_delete_database_not_found():
    """
    Test delete_database raises an exception when database is not found.
    """
    with patch("main.get_database", new=AsyncMock(return_value=None)):
        with pytest.raises(Exception) as excinfo:
            await delete_database("nonexistent-db", "test-account")

        assert "Database nonexistent-db not found" in str(excinfo.value)


@pytest.mark.asyncio
async def test_list_vhosts(mock_vhost_manager):
    """
    Test list_vhosts correctly returns vhost data.
    """
    mock_vhosts = [
        Vhost(
            id=1,
            status="provisioned",
            created_at="2023-01-01T12:00:00Z",
            updated_at="2023-01-01T12:00:00Z",
            external_host="app-123.aptible.com",
            links={
                "service": {"href": "https://api.aptible.com/services/123"},
            },
        ),
        Vhost(
            id=2,
            status="provisioning",
            created_at="2023-01-02T12:00:00Z",
            updated_at="2023-01-02T12:00:00Z",
            external_host="app-456.aptible.com",
            links={
                "service": {"href": "https://api.aptible.com/services/456"},
            },
        ),
    ]
    mock_vhost_manager.list = AsyncMock(return_value=mock_vhosts)

    result = await list_vhosts()

    mock_vhost_manager.list.assert_called_once()
    assert len(result) == 2
    assert result[0]["id"] == 1
    assert result[0]["external_host"] == "app-123.aptible.com"
    assert result[0]["status"] == "provisioned"
    assert result[1]["id"] == 2
    assert result[1]["external_host"] == "app-456.aptible.com"


@pytest.mark.asyncio
async def test_get_vhost_success(mock_vhost_manager):
    """
    Test get_vhost successfully retrieves a vhost by ID.
    """
    mock_vhost = Vhost(
        id=1,
        status="provisioned",
        created_at="2023-01-01T12:00:00Z",
        updated_at="2023-01-01T12:00:00Z",
        external_host="app-123.aptible.com",
        links={
            "service": {"href": "https://api.aptible.com/services/123"},
        },
    )
    mock_vhost_manager.get = AsyncMock(return_value=mock_vhost)

    result = await get_vhost("1")

    mock_vhost_manager.get.assert_called_once_with("1")
    assert result["id"] == 1
    assert result["external_host"] == "app-123.aptible.com"
    assert result["status"] == "provisioned"


@pytest.mark.asyncio
async def test_get_vhost_not_found(mock_vhost_manager):
    """
    Test get_vhost returns None when vhost is not found.
    """
    mock_vhost_manager.get = AsyncMock(return_value=None)

    result = await get_vhost("999")

    mock_vhost_manager.get.assert_called_once_with("999")
    assert result is None


@pytest.mark.asyncio
async def test_create_vhost_success(mock_service_manager, mock_vhost_manager):
    """
    Test create_vhost successfully creates a new vhost.
    """
    mock_app_data = {
        "id": 1,
        "handle": "test-app",
        "status": "provisioned",
        "created_at": "2023-01-01T12:00:00Z",
        "updated_at": "2023-01-01T12:00:00Z",
        "links": {"account": {"href": "https://api.aptible.com/accounts/123"}},
    }

    mock_services = [
        Service(
            id=123,
            handle="web",
            process_type="web",
            container_count=2,
            container_memory_limit_mb=1024,
            created_at="2023-01-01T12:00:00Z",
            updated_at="2023-01-01T12:00:00Z",
            links={
                "app": {"href": "https://api.aptible.com/apps/1"},
            },
        ),
        Service(
            id=456,
            handle="worker",
            process_type="worker",
            container_count=1,
            container_memory_limit_mb=512,
            created_at="2023-01-01T12:00:00Z",
            updated_at="2023-01-01T12:00:00Z",
            links={
                "app": {"href": "https://api.aptible.com/apps/1"},
            },
        ),
    ]

    mock_vhost = Vhost(
        id=42,
        status="provisioning",
        created_at="2023-01-01T12:00:00Z",
        updated_at="2023-01-01T12:00:00Z",
        external_host="app-123.aptible.com",
        links={
            "service": {"href": "https://api.aptible.com/services/123"},
        },
    )

    mock_service_manager.list_by_app = AsyncMock(return_value=mock_services)
    mock_vhost_manager.create = AsyncMock(return_value=mock_vhost)

    with patch("main.get_app", new=AsyncMock(return_value=mock_app_data)):
        result = await create_vhost("test-app", "web", "test-account")

        mock_service_manager.list_by_app.assert_called_once_with(1)
        mock_vhost_manager.create.assert_called_once_with({"service_id": 123})

        assert result["id"] == 42
        assert result["external_host"] == "app-123.aptible.com"
        assert result["status"] == "provisioning"


@pytest.mark.asyncio
async def test_create_vhost_app_not_found():
    """
    Test create_vhost raises an exception when app is not found.
    """

    with patch("main.get_app", new=AsyncMock(return_value=None)):
        with pytest.raises(Exception) as excinfo:
            await create_vhost("nonexistent-app", "web", "test-account")

        assert "App nonexistent-app not found" in str(excinfo.value)


@pytest.mark.asyncio
async def test_create_vhost_service_not_found(mock_service_manager):
    """
    Test create_vhost raises an exception when service is not found.
    """

    mock_app_data = {
        "id": 1,
        "handle": "test-app",
        "status": "provisioned",
        "created_at": "2023-01-01T12:00:00Z",
        "updated_at": "2023-01-01T12:00:00Z",
        "links": {"account": {"href": "https://api.aptible.com/accounts/123"}},
    }

    mock_services = []

    mock_service_manager.list_by_app = AsyncMock(return_value=mock_services)

    with patch("main.get_app", new=AsyncMock(return_value=mock_app_data)):
        with pytest.raises(Exception) as excinfo:
            await create_vhost("test-app", "nonexistent-service", "test-account")

        mock_service_manager.list_by_app.assert_called_once_with(1)
        assert (
            "No service with handle nonexistent-service found in app test-app"
            in str(excinfo.value)
        )


@pytest.mark.asyncio
async def test_delete_vhost(mock_vhost_manager):
    """
    Test delete_vhost successfully calls the manager.
    """

    mock_vhost_manager.delete_vhost = AsyncMock()

    await delete_vhost(42)
    mock_vhost_manager.delete_vhost.assert_called_once_with(42)


@pytest.mark.asyncio
async def test_list_services(mock_service_manager):
    """
    Test list_services returns services for an app.
    """

    mock_app_data = {
        "id": 1,
        "handle": "test-app",
        "status": "provisioned",
        "created_at": "2023-01-01T12:00:00Z",
        "updated_at": "2023-01-01T12:00:00Z",
        "links": {"account": {"href": "https://api.aptible.com/accounts/123"}},
    }

    mock_services = [
        Service(
            id=1,
            handle="web",
            process_type="web",
            container_count=2,
            container_memory_limit_mb=1024,
            created_at="2023-01-01T12:00:00Z",
            updated_at="2023-01-01T12:00:00Z",
            links={
                "app": {"href": "https://api.aptible.com/apps/1"},
            },
        ),
        Service(
            id=2,
            handle="worker",
            process_type="worker",
            container_count=1,
            container_memory_limit_mb=512,
            created_at="2023-01-02T12:00:00Z",
            updated_at="2023-01-02T12:00:00Z",
            links={
                "app": {"href": "https://api.aptible.com/apps/1"},
            },
        ),
    ]

    mock_service_manager.list_by_app = AsyncMock(return_value=mock_services)

    with patch("main.get_app", new=AsyncMock(return_value=mock_app_data)):
        result = await list_services("test-app", "test-account")

        mock_service_manager.list_by_app.assert_called_once_with(1)

        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[0]["handle"] == "web"
        assert result[0]["process_type"] == "web"
        assert result[0]["container_count"] == 2
        assert result[1]["id"] == 2
        assert result[1]["handle"] == "worker"


@pytest.mark.asyncio
async def test_list_services_app_not_found():
    """
    Test list_services raises an exception when app is not found.
    """

    with patch("main.get_app", new=AsyncMock(return_value=None)):
        with pytest.raises(Exception) as excinfo:
            await list_services("nonexistent-app", "test-account")

        assert "App nonexistent-app not found" in str(excinfo.value)


@pytest.mark.asyncio
async def test_get_service_success(mock_service_manager):
    """
    Test get_service successfully retrieves a service.
    """

    mock_app_data = {
        "id": 1,
        "handle": "test-app",
        "status": "provisioned",
        "created_at": "2023-01-01T12:00:00Z",
        "updated_at": "2023-01-01T12:00:00Z",
        "links": {"account": {"href": "https://api.aptible.com/accounts/123"}},
    }

    mock_service = Service(
        id=1,
        handle="web",
        process_type="web",
        container_count=2,
        container_memory_limit_mb=1024,
        created_at="2023-01-01T12:00:00Z",
        updated_at="2023-01-01T12:00:00Z",
        links={
            "app": {"href": "https://api.aptible.com/apps/1"},
        },
    )

    mock_service_manager.get_by_handle_and_app = AsyncMock(return_value=mock_service)

    with patch("main.get_app", new=AsyncMock(return_value=mock_app_data)):
        result = await get_service("test-app", "web", "test-account")

        mock_service_manager.get_by_handle_and_app.assert_called_once_with("web", 1)

        assert result["id"] == 1
        assert result["handle"] == "web"
        assert result["process_type"] == "web"
        assert result["container_count"] == 2


@pytest.mark.asyncio
async def test_get_service_app_not_found():
    """
    Test get_service raises an exception when app is not found.
    """

    with patch("main.get_app", new=AsyncMock(return_value=None)):
        with pytest.raises(Exception) as excinfo:
            await get_service("nonexistent-app", "web", "test-account")

        assert "App nonexistent-app not found" in str(excinfo.value)


@pytest.mark.asyncio
async def test_get_service_not_found(mock_service_manager):
    """
    Test get_service raises an exception when service is not found.
    """

    mock_app_data = {
        "id": 1,
        "handle": "test-app",
        "status": "provisioned",
        "created_at": "2023-01-01T12:00:00Z",
        "updated_at": "2023-01-01T12:00:00Z",
        "links": {"account": {"href": "https://api.aptible.com/accounts/123"}},
    }

    mock_service_manager.get_by_handle_and_app = AsyncMock(return_value=None)

    with patch("main.get_app", new=AsyncMock(return_value=mock_app_data)):
        with pytest.raises(Exception) as excinfo:
            await get_service("test-app", "nonexistent-service", "test-account")

        mock_service_manager.get_by_handle_and_app.assert_called_once_with(
            "nonexistent-service", 1
        )
        assert (
            "No service with handle nonexistent-service found in app test-app"
            in str(excinfo.value)
        )


@pytest.mark.asyncio
async def test_scale_service_success(mock_service_manager):
    """
    Test scale_service successfully scales a service.
    """

    mock_service_data = {
        "id": 1,
        "handle": "web",
        "process_type": "web",
        "container_count": 2,
        "container_memory_limit_mb": 1024,
        "created_at": "2023-01-01T12:00:00Z",
        "updated_at": "2023-01-01T12:00:00Z",
        "links": {"app": {"href": "https://api.aptible.com/apps/1"}},
    }

    mock_updated_service = Service(
        id=1,
        handle="web",
        process_type="web",
        container_count=4,
        container_memory_limit_mb=2048,
        created_at="2023-01-01T12:00:00Z",
        updated_at="2023-01-03T12:00:00Z",
        links={
            "app": {"href": "https://api.aptible.com/apps/1"},
        },
    )

    mock_service_manager.scale = AsyncMock(return_value=mock_updated_service)

    with patch("main.get_service", new=AsyncMock(return_value=mock_service_data)):
        result = await scale_service(
            "test-app",
            "web",
            container_count=4,
            container_memory_limit_mb=2048,
            account_handle="test-account",
        )

        mock_service_manager.scale.assert_called_once_with(1, 4, 2048)

        assert result["id"] == 1
        assert result["handle"] == "web"
        assert result["container_count"] == 4
        assert result["container_memory_limit_mb"] == 2048


@pytest.mark.asyncio
async def test_scale_service_no_parameters():
    """
    Test scale_service raises an exception when no scaling parameters are provided.
    """
    with pytest.raises(ValueError) as excinfo:
        await scale_service("test-app", "web", account_handle="test-account")

    assert "Must specify at least one of container_count or container_size" in str(
        excinfo.value
    )


@pytest.mark.asyncio
async def test_list_service_vhosts(mock_vhost_manager):
    """
    Test list_service_vhosts returns vhosts for a service.
    """

    mock_service_data = {
        "id": 1,
        "handle": "web",
        "process_type": "web",
        "container_count": 2,
        "container_memory_limit_mb": 1024,
        "created_at": "2023-01-01T12:00:00Z",
        "updated_at": "2023-01-01T12:00:00Z",
        "links": {"app": {"href": "https://api.aptible.com/apps/1"}},
    }

    mock_vhosts = [
        Vhost(
            id=1,
            status="provisioned",
            created_at="2023-01-01T12:00:00Z",
            updated_at="2023-01-01T12:00:00Z",
            external_host="app-123.aptible.com",
            links={
                "service": {"href": "https://api.aptible.com/services/1"},
            },
        ),
        Vhost(
            id=2,
            status="provisioned",
            created_at="2023-01-02T12:00:00Z",
            updated_at="2023-01-02T12:00:00Z",
            external_host="custom-domain.example.com",
            links={
                "service": {"href": "https://api.aptible.com/services/1"},
            },
        ),
    ]

    mock_vhost_manager.list_by_service = AsyncMock(return_value=mock_vhosts)

    with patch("main.get_service", new=AsyncMock(return_value=mock_service_data)):
        with patch("main.Service.model_validate") as mock_validate:
            mock_service = Mock()
            mock_service.id = 1
            mock_validate.return_value = mock_service

            result = await list_service_vhosts("test-app", "web", "test-account")

            mock_vhost_manager.list_by_service.assert_called_once_with(1)

            assert len(result) == 2
            assert result[0]["id"] == 1
            assert result[0]["external_host"] == "app-123.aptible.com"
            assert result[1]["id"] == 2
            assert result[1]["external_host"] == "custom-domain.example.com"
