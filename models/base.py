from typing import Any, Dict, Generic, List, Optional, Type, TypeVar
from pydantic import BaseModel, Field, model_validator

T = TypeVar('T', bound=BaseModel)
ID = TypeVar('ID')


class ResourceBase(BaseModel):
    """
    Base model for all API resources.
    """
    id: str | int = Field(..., description="Resource unique identifier")
    links: Dict[str, Any] = Field({}, description="Links to related resources")
    
    class Config:
        extra = "allow"
    
    @model_validator(mode='before')
    @classmethod
    def transform_links(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform _links to links for API compatibility.
        """
        if isinstance(data, dict) and '_links' in data:
            data['links'] = data.pop('_links')
        return data


class ResourceManager(Generic[T, ID]):
    """
    Base class for resource managers providing CRUD operations.
    """
    resource_name: str
    resource_model: Type[T]
    resource_url: str

    name_field: str = "handle"
    
    def __init__(self, api_client):
        self.api_client = api_client
    
    async def list(self, **kwargs) -> List[T]:
        """
        List all resources.
        """
        # ?per_page=5000 is a hacky way to avoid pagination that we shouldn't keep long-term.
        # no_embed=true avoids some expensive/slow queries for data we're not using anyway.
        response = self.api_client.get(f"{self.resource_url}?per_page=5000&no_embed=true")
        items = response["_embedded"][self.resource_name]
        return [self.resource_model.model_validate(item) for item in items]
    
    async def get(self, identifier: ID, **kwargs) -> Optional[T]:
        """
        Get a specific resource by semi-unique identifier (usually handle).
        """
        items = await self.list(**kwargs)
        for item in items:
            if getattr(item, self.name_field) == identifier:
                return item

    async def get_by_id(self, id: str | int, **kwargs) -> Optional[T]:
        """
        Get a specific resource by ID.

        Note that sometimes the ID is a str (UUID) and
        sometimes it's an int. It's on you to pass in
        the correct format! If you pass in an int as a str
        or a UUID as a UUID, there will not be a match!
        """
        items = await self.list(**kwargs)
        for item in items:
            if item.id == id:
                return item
        return None
    
    async def create(self, data: Dict[str, Any]) -> T:
        """
        Create a new resource.
        """
        response = self.api_client.post(f"{self.resource_url}", data)
        return self.resource_model.model_validate(response)
    
    async def delete(self, resource_id: str) -> None:
        """
        Delete a resource by ID.
        """
        self.api_client.delete(f"{self.resource_url}/{resource_id}")
