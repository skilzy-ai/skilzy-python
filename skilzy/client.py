# skilzy/client.py

import httpx
from typing import Optional, List
from pathlib import Path
from . import models
from . import errors


class SkilzyClient:
    """Main client for interacting with the Skilzy API."""
    
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        base_url: str = "https://api.skilzy.ai", 
        verify_ssl: bool = True
    ):
        import os
        from . import config
        
        # Determine API key from multiple sources, in order of priority:
        # 1. Directly provided argument
        # 2. SKILZY_API_KEY environment variable
        # 3. Saved config file
        final_api_key = (
            api_key or 
            os.environ.get("SKILZY_API_KEY") or 
            config.load_api_key()
        )

        self._base_url = base_url
        self._api_key = final_api_key
        self._verify_ssl = verify_ssl
        
        headers = {"User-Agent": f"skilzy-python-sdk/0.1.0"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        self._client = httpx.Client(
            base_url=self._base_url,
            headers=headers,
            verify=self._verify_ssl
        )

    def _handle_response(self, response: httpx.Response):
        """Centralized error handling for API responses."""
        if 200 <= response.status_code < 300:
            return response.json()
        
        # Map HTTP status codes to specific exception types
        error_map = {
            401: errors.SkilzyAuthenticationError,
            403: errors.SkilzyPermissionError,
            404: errors.SkilzyNotFound,
            409: errors.SkilzyConflictError,
        }
        
        error_class = error_map.get(response.status_code, errors.SkilzyAPIError)
        
        # Attempt to extract error message from response body
        try:
            message = response.json().get("message", "An unknown API error occurred.")
        except Exception:
            message = "Could not read error response from API."

        raise error_class(message, response.status_code)

    def search_skills(
        self, 
        q: str = None, 
        author: str = None, 
        keywords: Optional[List[str]] = None, 
        sort_by: str = "relevance", 
        page: int = 1, 
        limit: int = 10
    ) -> models.SkillSearchResult:
        """Search for skills in the registry."""
        params = {"page": page, "limit": limit, "sortBy": sort_by}
        
        if q:
            params['q'] = q
        if author:
            params['author'] = author
        if keywords:
            params['keywords'] = ",".join(keywords)
        
        response = self._client.get("/skills/search", params=params)
        data = self._handle_response(response)
        return models.SkillSearchResult(**data)

    def get_skill_details(self, author: str, skill_name: str) -> models.SkillDetail:
        """Get detailed information about a specific skill."""
        response = self._client.get(f"/skills/{author}/{skill_name}")
        data = self._handle_response(response)
        return models.SkillDetail(**data)

    def get_skill_version(
        self, 
        author: str, 
        skill_name: str, 
        version: str
    ) -> models.SkillVersion:
        """Get information about a specific version of a skill."""
        response = self._client.get(
            f"/skills/{author}/{skill_name}/versions/{version}"
        )
        data = self._handle_response(response)
        return models.SkillVersion(**data)

    def download_skill(
        self, 
        author: str, 
        skill_name: str, 
        version: str, 
        output_path: str
    ):
        """Download a skill package to a specified file path."""
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Use streaming to handle potentially large skill packages
            with httpx.stream(
                "GET",
                f"{self._base_url}/skills/{author}/{skill_name}/versions/{version}/download",
                headers=self._client.headers,
                follow_redirects=True,
                verify=self._verify_ssl,
                timeout=30.0
            ) as response:
                if response.status_code != 200:
                    raise errors.SkilzyAPIError(
                        f"Failed to download skill. Status code: {response.status_code}", 
                        response.status_code
                    )

                with open(output_path, "wb") as f:
                    for chunk in response.iter_bytes():
                        f.write(chunk)
        except httpx.ConnectError as e:
            raise errors.SkilzyAPIError(
                f"Connection to {self._base_url} failed: {e}", 
                status_code=503
            )

    def publish_skill(self, skill_package_path: str):
        """
        Publishes a new skill or version to the registry from a .skill package.
        This requires the client to be authenticated with an API key.
        """
        import zipfile
        from .errors import SkilzyError

        if not self._api_key:
            raise SkilzyError(
                "Authentication required: API key is not configured for the client."
            )

        try:
            # Extract manifest from zip file without full extraction for validation
            with zipfile.ZipFile(skill_package_path, 'r') as z:
                # Find skill.json regardless of root folder structure
                manifest_path_in_zip = next(
                    (s for s in z.namelist() 
                     if s.endswith('/skill.json') or s == 'skill.json'), 
                    None
                )
                if not manifest_path_in_zip:
                    raise SkilzyError(
                        "Invalid .skill package: skill.json not found in the archive."
                    )
                
                with z.open(manifest_path_in_zip) as manifest_file:
                    manifest_content_str = manifest_file.read().decode('utf-8')
        except (zipfile.BadZipFile, FileNotFoundError):
            raise SkilzyError(
                f"Could not open or read the skill package at '{skill_package_path}'."
            )

        # Prepare multipart form data for upload
        with open(skill_package_path, 'rb') as f:
            files = {
                'file': (Path(skill_package_path).name, f, 'application/zip'),
                'manifest': (None, manifest_content_str)
            }
            
            # Remove Content-Type header to let httpx set it for multipart data
            request_headers = self._client.headers.copy()
            request_headers.pop('Content-Type', None)
            
            response = self._client.post(
                "/skills/publish",
                files=files,
                headers=request_headers,
                timeout=90.0  # Extended timeout for file uploads
            )

        return self._handle_response(response)

    def get_my_skills(self) -> List[models.MySkill]:
        """
        Retrieves a list of all skills submitted by the authenticated user.
        Requires authentication.
        """
        from .errors import SkilzyError

        if not self._api_key:
            raise SkilzyError(
                "Authentication required: API key is not configured for the client."
            )

        response = self._client.get("/users/me/skills")
        data = self._handle_response(response)
        
        # Convert list of dictionaries to list of MySkill objects
        return [models.MySkill(**item) for item in data]

    def __del__(self):
        """Ensure the httpx client is properly closed when the object is destroyed."""
        if hasattr(self, '_client'):
            self._client.close()