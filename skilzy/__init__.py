# skilzy/__init__.py

"""
Official Python SDK for the Skilzy AI Skills Registry.
"""

__version__ = "0.1.0"

from .client import SkilzyClient
from .errors import SkilzyError, SkilzyNotFound, SkilzyAuthenticationError
from .models import (
    Skill,
    SkillSearchResult,
    SkillVersion,
    APIKey
)

# Import action functions for programmatic use
from .actions import (
    login,
    search,
    install,
    list_skills,
    remove_skill,
    sync_skills,
    publish,
    init,
    me_whoami,
    me_skills
)

__all__ = [
    # Client and error classes
    "SkilzyClient",
    "SkilzyError",
    "SkilzyNotFound",
    "SkilzyAuthenticationError",
    
    # Model classes
    "Skill",
    "SkillSearchResult",
    "SkillVersion",
    "APIKey",
    "MySkill",
     
    # Action functions (programmatic API)
    "login",
    "search",
    "install",
    "list_skills",
    "remove_skill",
    "sync_skills",
    "publish",
    "init",
    "me_whoami",
    "me_skills",
]
