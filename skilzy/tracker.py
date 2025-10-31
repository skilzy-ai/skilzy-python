# skilzy/tracker.py
import json
from pathlib import Path
from typing import Dict, Any, List

SKILL_TRACKING_FILE = "skilzy.json"


class SkillTracker:
    """Manages the skilzy.json tracking file for a project."""
    
    def __init__(self, project_root: Path):
        self.tracking_file_path = project_root / SKILL_TRACKING_FILE

    def initialize_tracking_file(self):
        """Creates an empty skilzy.json file if it doesn't exist.
        
        Returns:
            bool: True if file was created, False if it already existed.
        """
        if not self.tracking_file_path.exists():
            initial_content = {
                "version": "1.0",
                "skills": {}
            }
            self.tracking_file_path.write_text(json.dumps(initial_content, indent=2))
            return True
        return False

    def load_skills(self) -> Dict[str, Any]:
        """Loads the skills from the skilzy.json file.
        
        Returns:
            Dict[str, Any]: Skills dictionary, or empty dict if file doesn't exist 
                           or contains invalid JSON.
        """
        if not self.tracking_file_path.exists():
            return {}
        
        try:
            content = json.loads(self.tracking_file_path.read_text(encoding='utf-8'))
            return content.get("skills", {})
        except (json.JSONDecodeError, IOError):
            # Return empty dict on any file read or JSON parsing errors
            return {}

    def save_skills(self, skills: Dict[str, Any]):
        """Saves the skills dictionary back to the skilzy.json file.
        
        Maintains the file structure with version information to ensure
        compatibility with the expected format.
        
        Args:
            skills: Dictionary of skills to save.
            
        Raises:
            IOError: If the file cannot be written to.
        """
        try:
            content = {
                "version": "1.0",
                "skills": skills
            }
            self.tracking_file_path.write_text(json.dumps(content, indent=2))
        except IOError as e:
            raise IOError(f"Failed to write to {self.tracking_file_path}: {e}")

    def add_skill(self, skill_name: str, version: str, path: str, 
                  dependencies: List[str] = None, author: str = None):
        """Adds or updates a skill in the tracking file.
        
        Args:
            skill_name: Name of the skill to add/update.
            version: Version of the skill.
            path: File path to the skill.
            dependencies: Optional list of skill dependencies.
            author: Optional author information.
        """
        skills = self.load_skills()
        skill_entry = {
            "version": version,
            "path": path,
            "dependencies": dependencies or []
        }
        
        # Only add author field if provided to keep entries clean
        if author:
            skill_entry["author"] = author
            
        skills[skill_name] = skill_entry
        self.save_skills(skills)

    def remove_skill(self, skill_name: str) -> bool:
        """Removes a skill from the tracking file.
        
        Args:
            skill_name: Name of the skill to remove.
            
        Returns:
            bool: True if skill was found and removed, False otherwise.
        """
        skills = self.load_skills()
        if skill_name in skills:
            del skills[skill_name]
            self.save_skills(skills)
            return True
        return False

    def get_installed_skills(self) -> Dict[str, Any]:
        """Returns all currently installed skills.
        
        Returns:
            Dict[str, Any]: Dictionary of all installed skills with their metadata.
        """
        return self.load_skills()