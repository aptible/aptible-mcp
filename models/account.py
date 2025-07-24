from typing import Optional, List, Any
from pydantic import Field, computed_field

from models.base import ResourceBase, ResourceManager


class Account(ResourceBase):
    """
    Aptible Account (aka Environment) model
    """

    handle: str = Field(..., description="Resource handle (name)")
    created_at: str = Field(..., description="Account creation timestamp")
    updated_at: str = Field(..., description="Account last update timestamp")

    @computed_field
    def stack_id(self) -> Optional[int]:
        """
        Extract stack_id from _links.stack.href

        Example: _links.stack.href = "https://api.aptible.com/stacks/1234"
        """
        if not self.links or "stack" not in self.links:
            return None

        href = self.links.get("stack", {}).get("href")
        if not href:
            return None

        return int(href.split("/")[-1])


class AccountManager(ResourceManager[Account, str]):
    """
    Manager for Account (aka Environment) resources
    """

    resource_name = "accounts"
    resource_model = Account
    resource_url = "/accounts"

    async def create(self, data: dict[str, Any]) -> Account:
        """
        Create a new account/environment
        """
        from main import stack_manager

        handle = data["handle"]
        if not handle:
            raise Exception("A handle is required.")
        stack_id = data["stack_id"]
        if not stack_id:
            raise Exception("A stack_id is required.")

        stack = await stack_manager.get_by_id(stack_id)
        if stack is None:
            raise Exception(f"Stack {stack_id} not found")

        account_type = "development" if not stack.organization_id else "production"

        data = {
            "handle": handle,
            "stack_id": stack.id,
            "type": account_type,
            "organization_id": self.api_client.organization_id(),
        }
        return await super().create(data)

    async def get_by_stack_id(self, stack_id: int) -> List[Account]:
        """
        Get accounts/environments for a stack by stack ID.
        """
        accounts = await self.list()
        return [account for account in accounts if account.stack_id == stack_id]
