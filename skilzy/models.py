# skilzy/models.py

from pydantic import BaseModel, Field, HttpUrl, model_validator
from typing import List, Optional, Dict
from datetime import datetime


class SkillBase(BaseModel):
    """Common fields shared across skill-related models."""
    name: str
    author: str
    description: str
    icon_url: Optional[HttpUrl] = Field(None, alias="iconUrl")
    keywords: List[str] = []


class Skill(SkillBase):
    """Represents a skill in search results or basic listings."""
    latest_version: str


class SkillSearchResult(BaseModel):
    """Represents the response from a skill search query with pagination."""
    data: List[Skill]
    total: int
    page: int
    limit: int


class SkillDetail(SkillBase):
    """Represents the detailed view of a skill with all its versions."""
    repository_url: Optional[HttpUrl] = Field(None, alias="repository_url")
    versions: List[str]
    updated_at: datetime = Field(..., alias="updatedAt")


class FilesystemPermission(BaseModel):
    """Defines filesystem access permissions for a skill."""
    access: str
    description: str


class Permissions(BaseModel):
    """Container for various permission types that a skill may require."""
    filesystem: Optional[FilesystemPermission] = None


class SkillVersion(BaseModel):
    """Represents a specific version of a skill with complete metadata."""
    name: str
    version: str
    description: str
    author: str
    license: str
    documentation_content: str = Field(..., alias="documentation_content")
    published_at: datetime = Field(..., alias="published_at")
    
    # Primary field for runtime dependencies
    runtime_details: Optional[Dict] = Field(None, alias="runtime_details")
    # Fallback field for API compatibility with non-compliant responses
    fallback_dependencies: Optional[Dict] = Field(None, alias="dependencies")
    
    permissions: Optional[Permissions] = None

    @model_validator(mode='after')
    def consolidate_dependencies(self) -> 'SkillVersion':
        """
        Ensures runtime_details is populated by falling back to the dependencies field
        when runtime_details is missing. This provides resilience against API variations.
        """
        if not self.runtime_details and self.fallback_dependencies:
            self.runtime_details = self.fallback_dependencies
        return self


class MySkillLatestVersion(BaseModel):
    """Represents the latest version information for a user's skill."""
    version: str
    status: str
    review_notes: Optional[str] = Field(None, alias="reviewNotes")
    published_at: Optional[datetime] = Field(None, alias="published_at")


class MySkill(BaseModel):
    """Represents a skill owned by the authenticated user with management details."""
    id: int
    name: str
    description: str
    repository_url: Optional[HttpUrl] = Field(None, alias="repository_url")
    license: str
    created_at: datetime = Field(..., alias="createdAt")
    latest_version: Optional[MySkillLatestVersion] = Field(None, alias="latestVersion")
    published_version_count: int = Field(..., alias="publishedVersionCount")
    total_versions: int = Field(..., alias="totalVersions")


class APIKey(BaseModel):
    """Represents API key metadata with security-safe information only."""
    id: int
    name: str
    prefix: str  # Only the prefix is exposed for security
    created_at: datetime = Field(..., alias="createdAt")
    last_used: Optional[datetime] = Field(None, alias="lastUsed")


class NewAPIKey(BaseModel):
    """Represents a newly created API key with the full key value visible."""
    key: str  # Full key is only shown once upon creation