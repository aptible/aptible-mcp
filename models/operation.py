from pydantic import Field
import requests
from typing import Dict, List, Any

from models.base import ResourceBase, ResourceManager


class Operation(ResourceBase):
    """
    Aptible Operation model.
    """

    resource_id: int = Field(
        ..., description="ID of the resource the operation was run against."
    )
    resource_type: str = Field(
        ..., description="Type of the resource the operation was run against."
    )
    type: str = Field(..., description="The type of operation run.")


class OperationManager(ResourceManager[Operation, str]):
    """
    Manager for Operations.
    """

    resource_name = "operations"
    resource_model = Operation
    resource_url = "/operations"

    async def logs(self, operation_id: int) -> str:
        """
        Get logs for an operation by fetching from the S3 URL endpoint.
        Returns the actual log content as a string.
        """
        # Make the request directly without going through api_client
        # since the result is not JSON.
        url = f"{self.api_client.api_url}/operations/{operation_id}/logs"
        headers = self.api_client._get_headers()

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        if not response.content:
            return f"No logs available for operation {operation_id} (empty response)"

        if response.status_code == 200:
            redirect_url = response.text
            log_response = requests.get(redirect_url)
            log_response.raise_for_status()
            if not log_response.content:
                return f"No logs available for operation {operation_id} (empty content from redirect URL)"
            return log_response.text

        return ""

    async def get_operations_for_app(self, app_id: int) -> List[Dict[str, Any]]:
        """
        Get recent operations for an app with ID, type, and status.
        """
        response = self.api_client.get(f"/apps/{app_id}/operations")
        operations = response.get("_embedded", {}).get("operations", [])
        return [
            {
                "id": op["id"],
                "type": op.get("type", "unknown"),
                "status": op.get("status", "unknown"),
            }
            for op in operations
        ]

    async def get_operations_for_database(
        self, database_id: int
    ) -> List[Dict[str, Any]]:
        """
        Get recent operations for a database with ID, type, and status.
        """
        response = self.api_client.get(f"/databases/{database_id}/operations")
        operations = response.get("_embedded", {}).get("operations", [])
        return [
            {
                "id": op["id"],
                "type": op.get("type", "unknown"),
                "status": op.get("status", "unknown"),
            }
            for op in operations
        ]

    async def get_operations_for_vhost(self, vhost_id: int) -> List[Dict[str, Any]]:
        """
        Get recent operations for a vhost with ID, type, and status.
        """
        response = self.api_client.get(f"/vhosts/{vhost_id}/operations")
        operations = response.get("_embedded", {}).get("operations", [])
        return [
            {
                "id": op["id"],
                "type": op.get("type", "unknown"),
                "status": op.get("status", "unknown"),
            }
            for op in operations
        ]
