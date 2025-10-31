# skilzy/actions.py

import sys
import subprocess
import zipfile
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any

from .client import SkilzyClient
from .errors import SkilzyError, SkilzyAuthenticationError
from .tracker import SkillTracker, SKILL_TRACKING_FILE
from . import config

# ===============================================
# Authentication Actions
# ===============================================

def login(api_key: str) -> Dict[str, str]:
    """
    Save the API key for authentication.
    
    Args:
        api_key: The Skilzy API key to save.
        
    Returns:
        Dict with status message.
        
    Raises:
        ValueError: If the API key is invalid (too short).
        IOError: If the key cannot be saved to the config file.
    """
    if not api_key or len(api_key) < 10:
        raise ValueError("Invalid API key provided. Key must be at least 10 characters.")
    
    config.save_api_key(api_key)
    print("✓ API key saved successfully.")
    return {"status": "success", "message": "API key saved successfully."}

def  me_whoami() -> Dict[str, str]:
    """
    Validate the currently configured API key.
    
    Returns:
        Dict with validation status and key prefix.
        
    Raises:
        ValueError: If no API key is found.
        SkilzyAuthenticationError: If the API key is invalid.
    """
    api_key = config.load_api_key()
    
    if not api_key:
        raise ValueError("No API key found. Please run login() first.")
    
    key_prefix = api_key[:8] + "..."
    print(f"Loaded API key prefix: {key_prefix}")
    
    print("Attempting to validate key with the API...")
    client = SkilzyClient()
    
    try:
        client.get_my_skills()
        print("✓ Validation successful: The API accepted this key.")
        return {"status": "success", "key_prefix": key_prefix}
    except SkilzyAuthenticationError:
        raise SkilzyAuthenticationError(
            "Validation failed: The API rejected this key (401 Unauthorized). "
            "Please verify this key is correct or re-run login().",
            401
        )

# ===============================================
# Skill Discovery Actions
# ===============================================

def search(
    query: str,
    author: Optional[str] = None,
    keywords: Optional[List[str]] = None,
    sort_by: str = "relevance",
    page: int = 1,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Search for skills in the Skilzy Registry.
    
    Args:
        query: The search query string.
        author: Optional author username to filter by.
        keywords: Optional list of keywords to filter by.
        sort_by: Sort method (default: "relevance").
        page: Page number for pagination (default: 1).
        limit: Number of results per page (default: 10).
        
    Returns:
        List of skill dictionaries matching the search criteria.
        
    Raises:
        SkilzyError: If the API request fails.
    """
    client = SkilzyClient()
    print(f"Searching for '{query}'...")
    
    results = client.search_skills(
        q=query,
        author=author,
        keywords=keywords,
        sort_by=sort_by,
        page=page,
        limit=limit
    )
    
    if not results.data:
        print("No skills found matching your criteria.")
        return []
    
    print(f"Found {results.total} skills:")
    output_data = []
    for skill in results.data:
        print(f"  - {skill.author}/{skill.name} (v{skill.latest_version}): {skill.description}")
        output_data.append(skill.dict())
    
    return output_data

# ===============================================
# Skill Installation Actions
# ===============================================

def install(
    skill_name: str,
    path: Optional[str] = None,
    overwrite: bool = False,
    cat: bool = False,
    insecure: bool = False,
    project_root: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Download and install a skill to the local filesystem.
    
    Args:
        skill_name: Full skill name in format 'author/skill-name'.
        path: Optional custom installation path (relative to project_root).
        overwrite: If True, replace existing installation.
        cat: If True, print the SKILL.md content after installation.
        insecure: If True, disable SSL certificate verification.
        project_root: Optional project root path (defaults to current directory).
        
    Returns:
        Dict with installation details (status, skill, version, path).
        
    Raises:
        ValueError: If skill_name format is invalid.
        FileExistsError: If installation directory exists and overwrite=False.
        SkilzyError: If API requests fail.
    """
    if not skill_name or '/' not in skill_name:
        raise ValueError("Invalid skill name format. Expected 'author/skill-name'.")

    author, name = skill_name.split('/', 1)
    
    root = project_root or Path.cwd()
    tracker = SkillTracker(root)
    
    if not tracker.tracking_file_path.exists():
        print(f"Info: Tracking file '{SKILL_TRACKING_FILE}' not found. Creating a new one.")
        tracker.initialize_tracking_file()

    client = SkilzyClient(verify_ssl=not insecure)
    install_dir = Path(path) if path else root / "skills" / name

    if install_dir.exists():
        if not overwrite:
            raise FileExistsError(
                f"Directory '{install_dir.resolve()}' already exists. "
                "Use overwrite=True to replace it or specify a different path."
            )
        print(f"Warning: Overwriting existing directory '{install_dir.resolve()}'.")
        shutil.rmtree(install_dir)

    try:
        print(f"Fetching details for {author}/{name}...")
        skill_details = client.get_skill_details(author=author, skill_name=name)
        latest_version = skill_details.versions[0]
        print(f"Found latest version: {latest_version}")

        version_details = client.get_skill_version(author=author, skill_name=name, version=latest_version)
        dependencies = version_details.runtime_details.get("python", []) if version_details.runtime_details else []

        if dependencies:
            print(f"Installing {len(dependencies)} Python dependencies...")
            for dep in dependencies:
                try:
                    subprocess.check_call(
                        [sys.executable, "-m", "pip", "install", dep],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.PIPE
                    )
                except subprocess.CalledProcessError as e:
                    print(f"  Warning: Failed to install dependency '{dep}'")

        install_dir.mkdir(parents=True, exist_ok=True)
        package_path = install_dir / f"{name}.tmp.skill"
        
        print("Downloading skill package...")
        client.download_skill(author=author, skill_name=name, version=latest_version, output_path=str(package_path))
        
        print("Extracting skill contents...")
        with zipfile.ZipFile(package_path, 'r') as zf:
            zf.extractall(install_dir)
        package_path.unlink()

        # Handle nested directory structure
        skill_json_path = next(install_dir.rglob("skill.json"), None)
        if not skill_json_path:
            raise Exception("Invalid package: skill.json not found.")

        source_dir = skill_json_path.parent
        if source_dir != install_dir:
            print("Correcting nested directory structure...")
            for item in source_dir.iterdir():
                shutil.move(str(item), str(install_dir / item.name))
            shutil.rmtree(source_dir)

        relative_path = str(install_dir.relative_to(root))
        tracker.add_skill(
            skill_name=skill_name,
            version=latest_version,
            path=relative_path,
            dependencies=dependencies,
            author=author
        )
        
        print(f"\n✓ Successfully installed '{skill_name}' v{latest_version}")
        print(str(install_dir.resolve()))
        print(f"Updated '{SKILL_TRACKING_FILE}'.")

        if cat:
            skill_md_path = install_dir / "SKILL.md"
            if skill_md_path.exists():
                print("\n--- SKILL.md Content ---")
                print(skill_md_path.read_text(encoding='utf-8'))
                print("------------------------")
            else:
                print("\nWarning: SKILL.md not found in the skill package.")

        return {
            "status": "success",
            "skill": skill_name,
            "version": latest_version,
            "path": str(install_dir.resolve())
        }

    except Exception as e:
        if install_dir.exists():
            shutil.rmtree(install_dir)
        raise e

def sync_skills(
    force: bool = False,
    insecure: bool = False,
    project_root: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Install all skills listed in skilzy.json (similar to 'npm install').
    
    Args:
        force: If True, reinstall all skills even if they exist.
        insecure: If True, disable SSL certificate verification.
        project_root: Optional project root path (defaults to current directory).
        
    Returns:
        Dict with sync summary (success_count, skip_count, error_count).
        
    Raises:
        FileNotFoundError: If skilzy.json tracking file doesn't exist.
    """
    root = project_root or Path.cwd()
    tracker = SkillTracker(root)

    if not tracker.tracking_file_path.exists():
        raise FileNotFoundError(
            f"Tracking file '{SKILL_TRACKING_FILE}' not found. "
            "Run 'skilzy init' to create one, or 'skilzy install <skill>' to install your first skill."
        )

    installed_skills = tracker.get_installed_skills()
    
    if not installed_skills:
        print(f"No skills found in '{SKILL_TRACKING_FILE}'. Nothing to sync.")
        return {"success_count": 0, "skip_count": 0, "error_count": 0}

    client = SkilzyClient(verify_ssl=not insecure)
    total_skills = len(installed_skills)
    print(f"Found {total_skills} skill(s) in '{SKILL_TRACKING_FILE}'\n")

    success_count = 0
    skip_count = 0
    error_count = 0

    for idx, (skill_name, skill_info) in enumerate(installed_skills.items(), 1):
        print(f"[{idx}/{total_skills}] Processing '{skill_name}'...")
        
        version = skill_info.get("version")
        path_str = skill_info.get("path", "")
        dependencies = skill_info.get("dependencies", [])
        stored_author = skill_info.get("author")
        install_dir = root / path_str

        needs_install = force or not install_dir.exists() or not (install_dir / "skill.json").exists()

        if not needs_install:
            print(f"  ✓ Already installed at '{install_dir.relative_to(root)}'")
            skip_count += 1
            continue

        try:
            if '/' in skill_name:
                author, name = skill_name.split('/', 1)
            elif stored_author:
                author = stored_author
                name = skill_name
            else:
                print(f"  Warning: Cannot determine author for '{skill_name}'. Please reinstall this skill.")
                print(f"  Run: remove_skill('{skill_name}', force=True) then install('<author/{skill_name}')")
                error_count += 1
                continue

            if install_dir.exists() and force:
                print(f"  Removing existing installation...")
                shutil.rmtree(install_dir)

            if dependencies:
                print(f"  Installing {len(dependencies)} Python dependencies...")
                for dep in dependencies:
                    try:
                        subprocess.check_call(
                            [sys.executable, "-m", "pip", "install", dep],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE
                        )
                    except subprocess.CalledProcessError:
                        print(f"    Warning: Failed to install dependency '{dep}'")

            install_dir.mkdir(parents=True, exist_ok=True)
            package_path = install_dir / f"{name}.tmp.skill"

            print(f"  Downloading version {version}...")
            client.download_skill(author=author, skill_name=name, version=version, output_path=str(package_path))

            print(f"  Extracting...")
            with zipfile.ZipFile(package_path, 'r') as zf:
                zf.extractall(install_dir)
            package_path.unlink()

            skill_json_path = next(install_dir.rglob("skill.json"), None)
            if not skill_json_path:
                raise Exception("Invalid package: skill.json not found.")

            source_dir = skill_json_path.parent
            if source_dir != install_dir:
                for item in source_dir.iterdir():
                    shutil.move(str(item), str(install_dir / item.name))
                shutil.rmtree(source_dir)

            print(f"  ✓ Successfully synced '{skill_name}' v{version}")
            success_count += 1

        except SkilzyError as e:
            print(f"  ✗ API Error: {e}")
            error_count += 1
        except Exception as e:
            print(f"  ✗ Error: {e}")
            if install_dir.exists():
                shutil.rmtree(install_dir, ignore_errors=True)
            error_count += 1

        print("")

    print("=" * 50)
    print("Sync Summary:")
    print(f"  ✓ Successfully synced: {success_count}")
    print(f"  ⊘ Skipped (already installed): {skip_count}")
    if error_count > 0:
        print(f"  ✗ Errors: {error_count}")
    print("=" * 50)

    return {
        "success_count": success_count,
        "skip_count": skip_count,
        "error_count": error_count
    }

# ===============================================
# Skill Management Actions
# ===============================================

def list_skills(project_root: Optional[Path] = None) -> Dict[str, Dict[str, Any]]:
    """
    List all skills tracked in the local skilzy.json file.
    
    Args:
        project_root: Optional project root path (defaults to current directory).
        
    Returns:
        Dict of installed skills with their metadata.
        
    Raises:
        FileNotFoundError: If skilzy.json doesn't exist.
    """
    root = project_root or Path.cwd()
    tracker = SkillTracker(root)

    if not tracker.tracking_file_path.exists():
        raise FileNotFoundError(
            f"Tracking file '{SKILL_TRACKING_FILE}' not found. "
            "Run 'skilzy init' or 'skilzy install <skill>' to start tracking skills."
        )

    installed_skills = tracker.get_installed_skills()
    
    if not installed_skills:
        print(f"No skills are tracked in '{SKILL_TRACKING_FILE}'.")
        return {}

    print(f"{'Skill Name':<30} {'Version':<15} {'Path':<40} {'Dependencies'}")
    print("-" * 100)
    
    for name, details in sorted(installed_skills.items()):
        deps_count = len(details.get("dependencies", []))
        version = details.get("version", "N/A")
        path = details.get("path", "N/A")
        print(f"{name:<30} {version:<15} {path:<40} {deps_count}")

    return installed_skills

def remove_skill(
    skill_name: str,
    force: bool = False,
    project_root: Optional[Path] = None
) -> Dict[str, str]:
    """
    Remove a skill and update the skilzy.json tracking file.
    
    Args:
        skill_name: The name of the skill to remove (e.g., 'pdf-pro' or 'author/pdf-pro').
        force: If True, skip confirmation prompt.
        project_root: Optional project root path (defaults to current directory).
        
    Returns:
        Dict with status message.
        
    Raises:
        ValueError: If the skill is not tracked.
        FileNotFoundError: If skilzy.json doesn't exist.
    """
    root = project_root or Path.cwd()
    tracker = SkillTracker(root)
    installed_skills = tracker.get_installed_skills()
    
    # Try exact match first (for full author/skill-name format)
    skill_to_remove = installed_skills.get(skill_name)
    matched_key = skill_name
    
    # If not found, try matching just the skill name part (without author)
    if not skill_to_remove:
        for key in installed_skills.keys():
            if '/' in key:
                _, name_part = key.split('/', 1)
                if name_part == skill_name:
                    skill_to_remove = installed_skills[key]
                    matched_key = key
                    break
    
    if not skill_to_remove:
        raise ValueError(
            f"Skill '{skill_name}' is not tracked in '{SKILL_TRACKING_FILE}'."
        )

    skill_dir = root / skill_to_remove.get("path", "")
    
    if not skill_dir.exists() or not skill_dir.is_dir():
        print(f"Warning: Directory for '{matched_key}' not found at '{skill_dir.resolve()}'.")
        print("The skill may have been removed manually. Proceeding to update tracking file.")
    
    if not force:
        print(f"You are about to permanently remove the skill '{matched_key}'.")
        response = input("Are you sure? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            print("Removal cancelled.")
            return {"status": "cancelled"}
    
    if skill_dir.exists():
        shutil.rmtree(skill_dir)
        print(f"✓ Successfully removed skill directory '{skill_dir}'.")
    
    if tracker.remove_skill(matched_key):
        print(f"✓ Successfully untracked skill '{matched_key}' from '{SKILL_TRACKING_FILE}'.")
    
    return {"status": "success", "message": f"Skill '{matched_key}' removed successfully."}
def init(project_root: Optional[Path] = None) -> Dict[str, Any]:
    """
    Initialize a new skilzy.json tracking file in the specified directory.
    
    Args:
        project_root: Optional project root path (defaults to current directory).
        
    Returns:
        Dict with status and tracking file path.
     """
    root = project_root or Path.cwd()
    tracker = SkillTracker(root)
    
    if tracker.initialize_tracking_file():
        print(f"✓ Successfully created '{tracker.tracking_file_path}'.")
        return {"status": "created", "path": str(tracker.tracking_file_path)}
    else:
        print(f"'{tracker.tracking_file_path}' already exists.")
        return {"status": "exists", "path": str(tracker.tracking_file_path)}

# ===============================================
# Publishing Actions
# ===============================================

def publish(
    package_path: str,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Publish a new or updated skill to the Skilzy Registry.
    
    Args:
        package_path: Path to the packaged .skill file to publish.
        api_key: Optional API key (if not provided, uses saved key).
        
    Returns:
        Dict with publish response (skill, version, status).
        
    Raises:
        FileNotFoundError: If the package file doesn't exist.
        SkilzyAuthenticationError: If not authenticated.
        SkilzyError: If the API request fails.
    """
    package_file = Path(package_path)
    
    if not package_file.exists() or not package_file.is_file():
        raise FileNotFoundError(f"Skill package not found at '{package_path}'")
    
    client = SkilzyClient(api_key=api_key)
    
    if not client._api_key:
        raise SkilzyAuthenticationError(
            "You must be logged in to publish a skill. Please run login() first.",
            401
        )
    
    print(f"Publishing skill from '{package_path}'...")
    
    response = client.publish_skill(str(package_path))
    
    print("\n✓ Publish request successful!")
    print(f"  - Skill: {response.get('skill')}")
    print(f"   - Version: {response.get('version')}")
    print(f"  - Status: {response.get('status')}")
    
    return response

def me_skills(api_key: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all skills published by the authenticated user.
    
    Args:
        api_key: Optional API key (if not provided, uses saved key).
        
    Returns:
        List of skill dictionaries with their metadata.
        
    Raises:
        SkilzyAuthenticationError: If not authenticated.
        SkilzyError: If the API request fails.
    """
    client = SkilzyClient(api_key=api_key)
    
    if not client._api_key:
        raise SkilzyAuthenticationError(
            "You must be logged in. Please run login() first.",
            401
        )
    
    my_skills = client.get_my_skills()
    
    if not my_skills:
        print("You have not published any skills yet.")
        return []
    
    print(f"{'Name':<30} {'Latest Version':<15} {'Status':<20} {'Published/Total Versions'}")
    print("-" * 90)
    
    skills_data = []
    for skill in my_skills:
        status, version = "N/A", "N/A"
        if skill.latest_version:
            version = skill.latest_version.version
            status = skill.latest_version.status
        
        version_info = f"{skill.published_version_count}/{skill.total_versions}"
        print(f"{skill.name:<30} {version:<15} {status:<20} {version_info}")
        skills_data.append(skill.dict())
    
    return skills_data
