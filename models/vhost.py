from typing import List, Any
from pydantic import Field, computed_field

from models.base import ResourceBase, ResourceManager


class Vhost(ResourceBase):
    """
    Aptible Vhost model.
    """

    virtual_domain: str | None = Field(None, description="Virtual domain for the vhost")
    external_host: str | None = Field(..., description="External host for the vhost")
    created_at: str = Field(..., description="VHost creation timestamp")
    updated_at: str = Field(..., description="VHost last update timestamp")
    status: str = Field(..., description="Current status of the vhost")

    @computed_field
    def service_id(self) -> int:
        """
        Extract service_id from links.service.href
        """
        if not self.links or "service" not in self.links:
            raise Exception("Service is missing from links")

        href = self.links.get("service", {}).get("href")
        if not href:
            raise Exception("Service link is missing href")

        return int(href.split("/")[-1])


class VhostManager(ResourceManager[Vhost, str]):
    """
    Manager for Vhost resources.
    """

    resource_name = "vhosts"
    resource_model = Vhost
    resource_url = "/vhosts"

    async def create(self, data: dict[str, Any]) -> Vhost:
        """
        Create a new Vhost (aka Endpoint) for a service.
        """
        service_id = data["service_id"]
        if not service_id:
            raise Exception("A service_id is required.")

        data = {
            "service_id": service_id,
            "type": "http",
            "platform": "alb",
            "load_balancing_algorithm_type": "round_robin",
            "default": True,
            "acme": False,
            "internal": False,
        }

        response = self.api_client.post(f"/services/{service_id}/vhosts", data)
        vhost = self.resource_model.model_validate(response)

        operation_data = {"type": "provision"}
        response = self.api_client.post(
            f"/vhosts/{vhost.id}/operations", operation_data
        )
        self.api_client.wait_for_operation(response["id"])

        return vhost

    async def list_by_service(self, service_id: int) -> List[Vhost]:
        """
        List all vhosts for a specific service.
        """
        response = self.api_client.get(
            f"/services/{service_id}/vhosts?per_page=5000&no_embed=true"
        )
        items = response["_embedded"][self.resource_name]
        return [self.resource_model.model_validate(item) for item in items]

    async def delete_vhost(self, vhost_id: int) -> None:
        """
        Delete a vhost by ID.
        """
        vhost = await self.get_by_id(vhost_id)
        if not vhost:
            raise Exception(f"No vhost found with id {vhost_id}")

        operation_data = {"type": "deprovision"}
        response = self.api_client.post(
            f"/vhosts/{vhost_id}/operations", operation_data
        )
        self.api_client.wait_for_operation(response["id"])
