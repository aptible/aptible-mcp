import pytest
from unittest.mock import MagicMock, AsyncMock

from models.database import Database, DatabaseImage, DatabaseManager
from api_client import AptibleApiClient


@pytest.fixture
def mock_api_client():
    """
    Fixture providing a mock AptibleApiClient.
    """
    mock_client = MagicMock(spec=AptibleApiClient)
    return mock_client


@pytest.fixture
def database_manager(mock_api_client):
    """
    Fixture providing a DatabaseManager with a mock API client.
    """
    return DatabaseManager(mock_api_client)


@pytest.fixture
def sample_database_data():
    """
    Fixture providing sample database data for testing.
    """
    return {
        "id": 1,
        "handle": "test-db",
        "type": "postgresql",
        "created_at": "2023-01-01T12:00:00Z",
        "updated_at": "2023-01-01T12:00:00Z",
        "status": "provisioned",
        "_links": {
            "account": {"href": "https://api.aptible.com/accounts/123"},
            "database_image": {"href": "https://api.aptible.com/database_images/456"},
        },
    }


@pytest.fixture
def sample_database_image_data():
    """
    Fixture providing sample database image data for testing.
    """
    return {
        "id": 456,
        "type": "postgresql",
        "version": "14",
        "description": "PostgreSQL 14",
        "created_at": "2022-01-01T12:00:00Z",
        "updated_at": "2022-01-01T12:00:00Z",
        "_links": {},
    }


@pytest.fixture
def sample_operation_response():
    """
    Fixture providing a sample operation response.
    """
    return {"id": "operation-123"}


class TestDatabaseImage:
    """
    Tests for the DatabaseImage model.
    """

    def test_database_image_init(self, sample_database_image_data):
        """
        Test that DatabaseImage can be initialized from valid data.
        """
        db_image = DatabaseImage.model_validate(sample_database_image_data)

        assert db_image.id == 456
        assert db_image.type == "postgresql"
        assert db_image.version == "14"
        assert db_image.description == "PostgreSQL 14"


class TestDatabase:
    """
    Tests for the Database model.
    """

    def test_database_init(self, sample_database_data):
        """
        Test that Database can be initialized from valid data.
        """
        database = Database.model_validate(sample_database_data)

        assert database.id == 1
        assert database.handle == "test-db"
        assert database.type == "postgresql"
        assert database.created_at == "2023-01-01T12:00:00Z"
        assert database.updated_at == "2023-01-01T12:00:00Z"
        assert database.status == "provisioned"
        assert database.links == {
            "account": {"href": "https://api.aptible.com/accounts/123"},
            "database_image": {"href": "https://api.aptible.com/database_images/456"},
        }

    def test_transform_links(self, sample_database_data):
        """
        Test that _links is transformed to links during initialization.
        """
        database = Database.model_validate(sample_database_data)

        assert "_links" not in sample_database_data
        assert "links" in sample_database_data
        assert database.links == {
            "account": {"href": "https://api.aptible.com/accounts/123"},
            "database_image": {"href": "https://api.aptible.com/database_images/456"},
        }

    def test_account_id_computed_field(self, sample_database_data):
        """
        Test that the account_id computed field works correctly.
        """
        database = Database.model_validate(sample_database_data)

        assert database.account_id == 123

    def test_account_id_missing(self):
        """
        Test that account_id returns None when account is missing from links.
        """
        database_data = {
            "id": 1,
            "handle": "test-db",
            "type": "postgresql",
            "created_at": "2023-01-01T12:00:00Z",
            "updated_at": "2023-01-01T12:00:00Z",
            "status": "provisioned",
            "links": {},
        }

        database = Database.model_validate(database_data)

        assert database.account_id is None

    def test_account_id_missing_href(self):
        """
        Test that account_id returns None when account href is missing.
        """
        database_data = {
            "id": 1,
            "handle": "test-db",
            "type": "postgresql",
            "created_at": "2023-01-01T12:00:00Z",
            "updated_at": "2023-01-01T12:00:00Z",
            "status": "provisioned",
            "links": {"account": {}},
        }

        database = Database.model_validate(database_data)

        assert database.account_id is None

    def test_database_image_id_computed_field(self, sample_database_data):
        """
        Test that the database_image_id computed field works correctly.
        """
        database = Database.model_validate(sample_database_data)

        assert database.database_image_id == 456

    def test_database_image_id_missing(self):
        """
        Test that database_image_id returns None when database_image is missing from links.
        """
        database_data = {
            "id": 1,
            "handle": "test-db",
            "type": "postgresql",
            "created_at": "2023-01-01T12:00:00Z",
            "updated_at": "2023-01-01T12:00:00Z",
            "status": "provisioned",
            "links": {"account": {"href": "https://api.aptible.com/accounts/123"}},
        }

        database = Database.model_validate(database_data)

        assert database.database_image_id is None

    def test_database_image_id_missing_href(self):
        """
        Test that database_image_id returns None when database_image href is missing.
        """
        database_data = {
            "id": 1,
            "handle": "test-db",
            "type": "postgresql",
            "created_at": "2023-01-01T12:00:00Z",
            "updated_at": "2023-01-01T12:00:00Z",
            "status": "provisioned",
            "links": {
                "account": {"href": "https://api.aptible.com/accounts/123"},
                "database_image": {},
            },
        }

        database = Database.model_validate(database_data)

        assert database.database_image_id is None


class TestDatabaseManager:
    """
    Tests for the DatabaseManager class.
    """

    @pytest.mark.asyncio
    async def test_list_available_types(
        self, database_manager, mock_api_client, sample_database_image_data
    ):
        """
        Test list_available_types correctly returns database image data.
        """

        mock_api_client.get.return_value = {
            "_embedded": {"database_images": [sample_database_image_data]}
        }

        result = await database_manager.list_available_types()

        assert len(result) == 1
        assert isinstance(result[0], DatabaseImage)
        assert result[0].id == 456
        assert result[0].type == "postgresql"
        assert result[0].version == "14"

        mock_api_client.get.assert_called_once_with("/database_images")

    @pytest.mark.asyncio
    async def test_create_success(
        self,
        database_manager,
        mock_api_client,
        sample_database_data,
        sample_database_image_data,
        sample_operation_response,
    ):
        """
        Test that the create method successfully creates a database.
        """

        account_id = 123
        image_id = 456
        handle = "test-db"

        database_image = DatabaseImage.model_validate(sample_database_image_data)
        database_manager.list_available_types = AsyncMock(return_value=[database_image])

        mock_api_client.post.side_effect = [
            sample_database_data,
            sample_operation_response,
        ]

        mock_api_client.wait_for_operation = MagicMock()

        result = await database_manager.create(
            {"handle": handle, "account_id": account_id, "image_id": image_id}
        )

        assert isinstance(result, Database)
        assert result.id == 1
        assert result.handle == "test-db"
        assert result.type == "postgresql"

        database_manager.list_available_types.assert_called_once()
        mock_api_client.post.assert_any_call(
            f"/accounts/{account_id}/databases",
            {
                "handle": handle,
                "database_image_id": image_id,
                "type": "postgresql",
            },
        )
        mock_api_client.post.assert_any_call(
            f"/databases/{result.id}/operations", {"type": "provision"}
        )
        mock_api_client.wait_for_operation.assert_called_once_with(
            sample_operation_response["id"]
        )

    @pytest.mark.asyncio
    async def test_create_missing_handle(self, database_manager):
        """
        Test create raises an exception when handle is missing.
        """
        with pytest.raises(Exception) as excinfo:
            await database_manager.create(
                {"handle": None, "account_id": 123, "image_id": 456}
            )

        assert "A handle is required" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_create_missing_account_id(self, database_manager):
        """
        Test create raises an exception when account_id is missing.
        """
        with pytest.raises(Exception) as excinfo:
            await database_manager.create(
                {"handle": "test-db", "account_id": None, "image_id": 456}
            )

        assert "An account_id is required" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_create_missing_image_id(self, database_manager):
        """
        Test create raises an exception when image_id is missing.
        """
        with pytest.raises(Exception) as excinfo:
            await database_manager.create(
                {"handle": "test-db", "account_id": 123, "image_id": None}
            )

        assert "A image_id is required" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_create_image_not_found(self, database_manager):
        """
        Test create raises an exception when image_id is not found.
        """

        database_manager.list_available_types = AsyncMock(return_value=[])

        with pytest.raises(ValueError) as excinfo:
            await database_manager.create(
                {"handle": "test-db", "account_id": 123, "image_id": 999}
            )

        assert "No database image found with id 999" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_delete_by_handle_success(
        self,
        database_manager,
        mock_api_client,
        sample_database_data,
        sample_operation_response,
    ):
        """
        Test delete_by_handle successfully deletes a database.
        """

        database = Database.model_validate(sample_database_data)
        database_manager.get_by_id = AsyncMock(return_value=database)

        mock_api_client.post.return_value = sample_operation_response

        mock_api_client.wait_for_operation = AsyncMock()

        await database_manager.delete(database.id)

        mock_api_client.post.assert_called_once_with(
            f"/databases/{database.id}/operations", {"type": "deprovision"}
        )
        mock_api_client.wait_for_operation.assert_called_once_with(
            sample_operation_response["id"]
        )

    @pytest.mark.asyncio
    async def test_delete_by_handle_not_found(self, database_manager):
        """
        Test delete_by_handle raises an exception when database is not found.
        """

        database_manager.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(Exception) as excinfo:
            await database_manager.delete(0)

        assert "Database 0 not found" in str(excinfo.value)
