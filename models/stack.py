from typing import Optional
from pydantic import Field

from models.base import ResourceBase, ResourceManager


class Stack(ResourceBase):
    """
    Aptible Stack model
    """
    name: str = Field(..., description="Stack name")
    region: str = Field(..., description="Stack region")
    public: bool = Field(..., description="Is this stack shared?")
    created_at: str = Field(..., description="Stack creation timestamp")
    updated_at: str = Field(..., description="Stack last update timestamp")
    organization_id: Optional[str] = Field(..., description="Organization ID of the org that owns this stack.")


class StackManager(ResourceManager[Stack, str]):
    """
    Manager for Stack resources
    """
    resource_name = "stacks"
    resource_model = Stack
    resource_url = "/stacks"

    name_field = "name"
