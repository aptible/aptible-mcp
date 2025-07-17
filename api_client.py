import json
import jwt
import os
import requests
from requests.exceptions import HTTPError
from pathlib import Path
from typing import Any, Dict, Optional

APTIBLE_API_URL = os.environ.get("APTIBLE_API_URL", "https://api.aptible.com")
APTIBLE_AUTH_URL = os.environ.get("APTIBLE_AUTH_URL", "https://auth.aptible.com")
APTIBLE_TOKEN = os.environ.get("APTIBLE_TOKEN", None)


def fetch_public_key() -> str:
    """
    Gets the public key used for signing JWTs
    from the Aptible Auth API.
    """
    response = requests.get(APTIBLE_AUTH_URL)
    public_key = response.json()["public_key"]
    return public_key


class AptibleApiClient:
    """
    Aptible API client for making authenticated requests to the API.
    """
    def __init__(self, api_url: Optional[str] = None, auth_url: Optional[str] = None) -> None:
        self.api_url = api_url or APTIBLE_API_URL
        self.auth_url = auth_url or APTIBLE_AUTH_URL
        self._token = None
        
    def get_token(self) -> str:
        """
        Get authentication token.
        """
        if self._token:
            return self._token
            
        # Try to get from environment
        if APTIBLE_TOKEN:
            self._token = APTIBLE_TOKEN
            return self._token
            
        # Try to get from file
        home = Path.home()
        try:
            with open(home / ".aptible" / "tokens.json") as f:
                data = json.load(f)
                self._token = data[self.auth_url]
        except (FileNotFoundError, KeyError) as e:
            raise Exception("Authentication token not found. Please login to Aptible CLI first.")
            
        if not self._token:
            raise Exception("You are not logged in")
            
        return self._token

    def parsed_token(self) -> Dict[str, Any]:
        """
        Parse the authentication token.
        """
        token = self.get_token()
        public_key = fetch_public_key()
        kwargs = {
            'algorithms': ["RS256", "RS512"],
            'options': {
                'verify_signature': True,
                'verify_exp': True,
            },
            'leeway': 0,
        }
        return jwt.decode(token, public_key, **kwargs)

    def organization_id(self) -> str:
        """
        Get the organization ID for the logged in user.
        Since users may be a member of multiple orgs (but basically none are), we always choose
        the first organization ID.

        This function doesn't really belong with this client,
        it's just here right now because that's where the token is.
        If a better place for this arises, please move it!
        """
        response = requests.get(f"{APTIBLE_AUTH_URL}/organizations", headers=self._get_headers())
        response.raise_for_status()
        orgs = response.json()["_embedded"]["organizations"]
        if orgs == 0:
            raise Exception("Logged in user is not a member of any organizations.")
        return orgs[0]["id"]

    def _get_headers(self) -> Dict[str, str]:
        """
        Get headers for API requests
        """
        return {
            "Content-Type": "application/hal+json",
            "Authorization": f"Bearer {self.get_token()}",
        }
        
    def _build_url(self, path: str) -> str:
        """
        Build the full URL for the API from just a path.
        """
        return f"{self.api_url}{path}" if not path.startswith("http") else path
        
    def get(self, path: str) -> Any:
        """
        Make a GET request to Aptible API.
        """
        url = self._build_url(path)
        response = requests.get(url, headers=self._get_headers())
        response.raise_for_status()
        return response.json()
        
    def post(self, path: str, data: Any) -> Any:
        """
        Make a POST request to Aptible API.
        """
        url = self._build_url(path)
        response = requests.post(url, headers=self._get_headers(), json=data)
        response.raise_for_status()
        return response.json()
    
    def put(self, path: str, data: Any) -> Any:
        """
        Make a PUT request to Aptible API.
        """
        url = self._build_url(path)
        response = requests.put(url, headers=self._get_headers(), json=data)
        response.raise_for_status()
        return response.json()
        
    def delete(self, path: str) -> Any:
        """
        Make a DELETE request to Aptible API.
        """
        url = self._build_url(path)
        response = requests.delete(url, headers=self._get_headers())
        response.raise_for_status()
        
        # Some DELETE responses may not return content
        if response.status_code == 204 or not response.content:
            return None
            
        return response.json()
        
    def wait_for_operation(self, operation_id: str) -> None:
        """
        Waits on the operation to reach a completed state
        OR for the operation to be deleted (from a deprovision).
        """
        done_states = ["succeeded", "failed"]
        while True:
            try:
                response = self.get(f"/operations/{operation_id}")
            except HTTPError as e:
                if e.response.status_code == 404:
                    return None
                raise

            status = response.get("status", "unknown")
            if status in done_states:
                if status == "failed":
                    raise Exception(f"Operation {operation_id} failed: {response.get('message', 'No error message')}")
                return None