import pytest
from unittest.mock import MagicMock

from models.stack import Stack, StackManager
from api_client import AptibleApiClient


@pytest.fixture
def mock_api_client():
    """
    Fixture providing a mock AptibleApiClient.
    """
    mock_client = MagicMock(spec=AptibleApiClient)
    return mock_client


@pytest.fixture
def stack_manager(mock_api_client):
    """
    Fixture providing a StackManager with a mock API client.
    """
    return StackManager(mock_api_client)


@pytest.fixture
def sample_stack_data():
    """
    Fixture providing sample stack data for testing.
    """
    return {
        "id": 123,
        "name": "test-stack",
        "region": "us-east-1",
        "public": False,
        "created_at": "2023-01-01T12:00:00Z",
        "updated_at": "2023-01-01T12:00:00Z",
        "organization_id": "org-123",
        "_links": {
            "self": {"href": "https://api.aptible.com/stacks/123"},
            "apps": {"href": "https://api.aptible.com/stacks/123/apps"},
            "databases": {"href": "https://api.aptible.com/stacks/123/databases"},
        },
    }


@pytest.fixture
def sample_stacks_data():
    """
    Fixture providing sample data for multiple stacks.
    """
    return [
        {
            "id": 123,
            "name": "test-stack-1",
            "region": "us-east-1",
            "public": False,
            "created_at": "2023-01-01T12:00:00Z",
            "updated_at": "2023-01-01T12:00:00Z",
            "organization_id": "org-123",
            "_links": {
                "self": {"href": "https://api.aptible.com/stacks/123"},
                "apps": {"href": "https://api.aptible.com/stacks/123/apps"},
                "databases": {"href": "https://api.aptible.com/stacks/123/databases"},
            },
        },
        {
            "id": 456,
            "name": "test-stack-2",
            "region": "us-west-1",
            "public": True,
            "created_at": "2023-01-02T12:00:00Z",
            "updated_at": "2023-01-02T12:00:00Z",
            "organization_id": "org-456",
            "_links": {
                "self": {"href": "https://api.aptible.com/stacks/456"},
                "apps": {"href": "https://api.aptible.com/stacks/456/apps"},
                "databases": {"href": "https://api.aptible.com/stacks/456/databases"},
            },
        },
    ]


class TestStack:
    """
    Tests for the Stack model.
    """

    def test_stack_init(self, sample_stack_data):
        """
        Test that Stack can be initialized from valid data.
        """
        stack = Stack.model_validate(sample_stack_data)

        assert stack.id == 123
        assert stack.name == "test-stack"
        assert stack.region == "us-east-1"
        assert stack.public is False
        assert stack.created_at == "2023-01-01T12:00:00Z"
        assert stack.updated_at == "2023-01-01T12:00:00Z"
        assert stack.organization_id == "org-123"
        assert stack.links == {
            "self": {"href": "https://api.aptible.com/stacks/123"},
            "apps": {"href": "https://api.aptible.com/stacks/123/apps"},
            "databases": {"href": "https://api.aptible.com/stacks/123/databases"},
        }

    def test_transform_links(self, sample_stack_data):
        """
        Test that _links is transformed to links during initialization.
        """

        stack = Stack.model_validate(sample_stack_data)

        assert "_links" not in sample_stack_data
        assert "links" in sample_stack_data
        assert stack.links == {
            "self": {"href": "https://api.aptible.com/stacks/123"},
            "apps": {"href": "https://api.aptible.com/stacks/123/apps"},
            "databases": {"href": "https://api.aptible.com/stacks/123/databases"},
        }


class TestStackManager:
    """
    Tests for the StackManager class.
    """

    @pytest.mark.asyncio
    async def test_list(self, stack_manager, mock_api_client, sample_stacks_data):
        """
        Test that list correctly returns all stacks.
        """

        mock_api_client.get.return_value = {"_embedded": {"stacks": sample_stacks_data}}

        result = await stack_manager.list()

        assert len(result) == 2
        assert isinstance(result[0], Stack)
        assert result[0].id == 123
        assert result[0].name == "test-stack-1"
        assert result[0].region == "us-east-1"
        assert result[0].public is False
        assert result[1].id == 456
        assert result[1].name == "test-stack-2"
        assert result[1].region == "us-west-1"
        assert result[1].public is True

        mock_api_client.get.assert_called_once_with(
            "/stacks?per_page=5000&no_embed=true"
        )

    @pytest.mark.asyncio
    async def test_get_by_name_found(
        self, stack_manager, mock_api_client, sample_stacks_data
    ):
        """
        Test get method successfully retrieves a stack by name.
        """

        mock_api_client.get.return_value = {"_embedded": {"stacks": sample_stacks_data}}

        result = await stack_manager.get("test-stack-1")

        assert result is not None
        assert isinstance(result, Stack)
        assert result.id == 123
        assert result.name == "test-stack-1"
        assert result.region == "us-east-1"

        mock_api_client.get.assert_called_once_with(
            "/stacks?per_page=5000&no_embed=true"
        )

    @pytest.mark.asyncio
    async def test_get_by_name_not_found(
        self, stack_manager, mock_api_client, sample_stacks_data
    ):
        """
        Test get method returns None when stack is not found.
        """

        mock_api_client.get.return_value = {"_embedded": {"stacks": sample_stacks_data}}

        result = await stack_manager.get("nonexistent-stack")

        assert result is None

        mock_api_client.get.assert_called_once_with(
            "/stacks?per_page=5000&no_embed=true"
        )

    @pytest.mark.asyncio
    async def test_get_by_id(self, stack_manager, mock_api_client, sample_stacks_data):
        """
        Test get_by_id method successfully retrieves a stack by ID.
        """

        sample_stack = sample_stacks_data[0]
        mock_api_client.get.return_value = sample_stack

        result = await stack_manager.get_by_id(sample_stack["id"])

        assert result is not None
        assert isinstance(result, Stack)
        assert result.id == sample_stack["id"]
        assert result.name == sample_stack["name"]
        assert result.region == sample_stack["region"]

        mock_api_client.get.assert_called_once_with(f"/stacks/{sample_stack['id']}")
