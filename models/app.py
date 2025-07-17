from typing import Dict, Optional
from pydantic import Field, computed_field

from models.base import ResourceBase, ResourceManager


class App(ResourceBase):
    """
    Aptible App model.
    """
    handle: str = Field(..., description="Resource handle (name)")
    created_at: str = Field(..., description="App creation timestamp")
    updated_at: str = Field(..., description="App last update timestamp")
    status: str = Field(..., description="Current status of the app")
    
    # Services are not embedded directly in the app object
    # They're retrieved separately via the services endpoint

    @computed_field
    @property
    def account_id(self) -> int:
        """
        Extract account_id from _links.account.href

        Example: links.stack.href = "https://api.aptible.com/accounts/1234"
        """
        if not self.links or 'account' not in self.links:
            raise Exception("Account is missing from _links")

        href = self.links.get('account', {}).get('href')
        if not href:
            raise Exception("Account link is missing href")

        return int(href.split('/')[-1])


class AppManager(ResourceManager[App, str]):
    """
    Manager for App resources.
    """
    resource_name = "apps"
    resource_model = App
    resource_url = "/apps"
    
    async def get_services(self, app_id: str):
        """
        Get services for an app. This requires the service manager to be injected.
        """
        # This will be implemented in the main.py to avoid circular imports
        if not hasattr(self, "service_manager"):
            raise Exception("ServiceManager not injected into AppManager")
            
        return await self.service_manager.list_by_app(app_id)

    async def create(self, handle: str, account_id: str, docker_image: str = None) -> App:
        """
        Create a new app
        """
        data = {"handle": handle}
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
    
    async def configure(self, app_id: str, env: Dict[str, str]) -> None:
        """
        Configure an app with environment variables.
        """
        operation_data = {
            "type": "configure",
            "env": env
        }
        response = self.api_client.post(f"/apps/{app_id}/operations", operation_data)
        self.api_client.wait_for_operation(response["id"])
    
    async def deploy(self, app_id: str) -> None:
        """
        Trigger a deployment of an app. This assumes docker image deployment with an
        already set docker image.
        """
        operation_data = {"type": "deploy"}
        response = self.api_client.post(f"/apps/{app_id}/operations", operation_data)
        self.api_client.wait_for_operation(response["id"])
    
    async def delete(self, app_id: int, account_id: Optional[int] = None) -> None:
        """
        Delete an app by handle.
        """
        app = await self.get_by_id(app_id)
        if not app:
            raise Exception(f"App with ID {app_id} not found")

        if not app and account_id:
            all_apps = await self.list()
            apps = [a for a in all_apps if a.handle == app.handle and a.account_id == account_id]
            if apps:
                app = apps[0]
        
        if not app:
            raise Exception(f"No app found with handle {app.handle}")
        
        operation_data = {"type": "deprovision"}
        response = self.api_client.post(f"/apps/{app.id}/operations", operation_data)
        self.api_client.wait_for_operation(response["id"])
