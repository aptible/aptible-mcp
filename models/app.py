from typing import Dict, Optional, Any, TYPE_CHECKING
from pydantic import Field, computed_field

from models.base import ResourceBase, ResourceManager

if TYPE_CHECKING:
    from models import ServiceManager


class App(ResourceBase):
    """
    Aptible App model.
    """

    handle: str = Field(..., description="Resource handle (name)")
    created_at: str = Field(..., description="App creation timestamp")
    updated_at: str = Field(..., description="App last update timestamp")
    status: str = Field(..., description="Current status of the app")

    @computed_field
    def account_id(self) -> int:
        """
        Extract account_id from _links.account.href

        Example: links.stack.href = "https://api.aptible.com/accounts/1234"
        """
        if not self.links or "account" not in self.links:
            raise Exception("Account is missing from _links")

        href = self.links.get("account", {}).get("href")
        if not href:
            raise Exception("Account link is missing href")

        return int(href.split("/")[-1])


class AppManager(ResourceManager[App, str]):
    """
    Manager for App resources.
    """

    resource_name = "apps"
    resource_model = App
    resource_url = "/apps"
    service_manager: Optional["ServiceManager"] = None

    async def get_services(self, app_id: int):
        """
        Get services for an app. This requires the service manager to be injected.
        """
        if not self.service_manager:
            raise Exception("ServiceManager not injected into AppManager")

        return self.service_manager.list_by_app(app_id)

    async def create(self, data: Dict[str, Any]) -> App:
        """
        Create a new app.
        """
        handle = data.get("handle")
        if not handle:
            raise Exception("A handle is required.")
        account_id = data.get("account_id")
        if not account_id:
            raise Exception("An account_id is required.")
        docker_image = data.get("docker_image")

        response = self.api_client.post(f"/accounts/{account_id}/apps", data)
        app = self.resource_model.model_validate(response)

        if docker_image:
            env = {
                "FORCE_SSL": "1",
                "APTIBLE_DOCKER_IMAGE": docker_image,
            }
            await self.configure(app.id, env)
            await self.deploy(app.id)

        return app

    async def configure(self, app_id: int, env: Dict[str, str]) -> None:
        """
        Configure an app with environment variables.
        """
        operation_data = {"type": "configure", "env": env}
        response = self.api_client.post(f"/apps/{app_id}/operations", operation_data)
        self.api_client.wait_for_operation(response["id"])

    async def deploy(self, app_id: int) -> None:
        """
        Trigger a deployment of an app. This assumes docker image deployment with an
        already set docker image.
        """
        operation_data = {"type": "deploy"}
        response = self.api_client.post(f"/apps/{app_id}/operations", operation_data)
        self.api_client.wait_for_operation(response["id"])

    async def delete(self, app_id: int) -> None:
        """
        Delete an app by handle.
        """
        app = await self.get_by_id(app_id)
        if not app:
            raise Exception(f"App {app_id} not found")

        operation_data = {"type": "deprovision"}
        response = self.api_client.post(f"/apps/{app.id}/operations", operation_data)
        self.api_client.wait_for_operation(response["id"])
