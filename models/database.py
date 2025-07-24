from typing import Optional, List, Any
from pydantic import Field, computed_field

from models.base import ResourceBase, ResourceManager


class DatabaseImage(ResourceBase):
    """
    Database Images available for managed databases.
    """

    type: str = Field(..., description="Database type (postgresql, redis, etc)")
    version: str = Field(..., description="Database version")
    description: str = Field(..., description="Database description")


class Database(ResourceBase):
    """
    Aptible Database model.
    """

    handle: str = Field(..., description="Resource handle (name)")
    type: str = Field(..., description="Database type (postgresql, redis, etc)")
    created_at: str = Field(..., description="Database creation timestamp")
    updated_at: str = Field(..., description="Database last update timestamp")
    status: str = Field(..., description="Current status of the database")

    @computed_field
    def account_id(self) -> Optional[int]:
        """
        Extract account_id from _links.account.href

        Example: links.stack.href = "https://api.aptible.com/accounts/1234"
        """
        if not self.links or "account" not in self.links:
            return None

        href = self.links.get("account", {}).get("href")
        if not href:
            return None

        return int(href.split("/")[-1])

    @computed_field
    def database_image_id(self) -> Optional[int]:
        """
        Extract account_id from _links.database_image.href

        Example: links.stack.href = "https://api.aptible.com/database_images/1234"
        """
        if not self.links or "database_image" not in self.links:
            return None

        href = self.links.get("database_image", {}).get("href")
        if not href:
            return None

        return int(href.split("/")[-1])


class DatabaseManager(ResourceManager[Database, str]):
    """
    Manager for Database resources.
    """

    resource_name = "databases"
    resource_model = Database
    resource_url = "/databases"

    async def list_available_types(self) -> List[DatabaseImage]:
        """
        List available database types.
        """
        response = self.api_client.get("/database_images")
        items = response["_embedded"]["database_images"]
        return [DatabaseImage.model_validate(item) for item in items]

    async def create(self, data: dict[str, Any]) -> Database:
        """
        Create a new database.

        Asking for an image ID as an input runs a little bit against the grain
        of the format of other methods, where we use handles/names instead.
        However, the chosen database image is a combination of type and version,
        and asking the AI to consistently and reliably provide both in the
        exact way that they're formatted in our API seemed like too much.
        """
        handle = data["handle"]
        if not handle:
            raise Exception("A handle is required")
        account_id = data["account_id"]
        if not account_id:
            raise Exception("An account_id is required")
        image_id = data["image_id"]
        if not image_id:
            raise Exception("A image_id is required")

        images = await self.list_available_types()
        images = [img for img in images if img.id == image_id]
        if not images:
            raise ValueError(f"No database image found with id {image_id}")
        if len(images) > 1:
            raise ValueError(f"Multiple database images found with id {image_id}")
        image = images[0]
        data = {
            "handle": handle,
            "database_image_id": image_id,
            "type": image.type or "postgresql",
        }
        response = self.api_client.post(f"/accounts/{account_id}/databases", data)
        database = self.resource_model.model_validate(response)

        operation_data = {"type": "provision"}
        response = self.api_client.post(
            f"/databases/{database.id}/operations", operation_data
        )
        self.api_client.wait_for_operation(response["id"])

        return database

    async def delete_by_handle(
        self, handle: str, account_id: Optional[int] = None
    ) -> None:
        """
        Delete a database by handle.
        """
        database = await self.get(handle)

        if not database and account_id:
            all_databases = await self.list()
            # TODO: This be wrong.
            databases = [
                db
                for db in all_databases
                if db.handle == handle and db.account_id == account_id
            ]
            if databases:
                database = databases[0]

        if not database:
            raise Exception(f"No database found with handle {handle}")

        operation_data = {"type": "deprovision"}
        response = self.api_client.post(
            f"/databases/{database.id}/operations", operation_data
        )
        self.api_client.wait_for_operation(response["id"])
