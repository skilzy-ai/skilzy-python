# Skilzy Python SDK & CLI

[![PyPI version](https://badge.fury.io/py/skilzy.svg)](https://badge.fury.io/py/skilzy)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

The official Python SDK and command-line interface for interacting with the Skilzy AI Skills Registry.

This toolkit allows developers and AI agents to seamlessly discover, install, manage, and publish reusable skills through both a powerful CLI and a clean Python API.

---

## 🚀 Quick Start

### Installation

```bash
pip install skilzy
```

### CLI Usage

```bash
# Search for skills
skilzy search "pdf"

# Install a skill
skilzy install skilzy-admin/pdf-pro

# List installed skills
skilzy list
```

### Python API Usage

```python
import skilzy

# Search for skills
results = skilzy.search("pdf")

# Install a skill
skilzy.install("skilzy-admin/pdf-pro", overwrite=True)

# List installed skills
skilzy.list_skills()
```

---

## 📚 Table of Contents

- [Installation](#installation)
- [Python SDK (Programmatic API)](#python-sdk-programmatic-api)
  - [Basic Usage](#basic-usage)
  - [Available Functions](#available-functions)
  - [Error Handling](#error-handling)
- [CLI Reference](#cli-reference)
  - [General Commands](#general-commands)
  - [Publishing & Account Management](#publishing--account-management)
- [Examples](#examples)

---

## 🐍 Python SDK (Programmatic API)

The Skilzy SDK provides a clean, Pythonic interface for all registry operations.

### Basic Usage

Simply import the `skilzy` module to access all functionality:

```python
import skilzy

# All functions are available directly on the module
skilzy.search("automation")
skilzy.install("author/skill-name")
skilzy.list_skills()
```

### Available Functions

#### **Discovery & Search**

**`skilzy.search(query, author=None, keywords=None, sort_by="relevance", page=1, limit=10)`**

Search for skills in the registry.

```python
import skilzy

# Simple search
results = skilzy.search("pdf")

# Advanced search with filters
results = skilzy.search(
    query="data processing",
    author="skilzy-admin",
    keywords=["csv", "excel"],
    limit=20
)
```

**Returns:** List of skill dictionaries

---

#### **Installation & Management**

**`skilzy.init(project_root=None)`**

Initialize a new `skilzy.json` tracking file in the current directory.

```python
import skilzy

skilzy.init()
```

**Returns:** Dict with status and file path

---

**`skilzy.install(skill_name, path=None, overwrite=False, cat=False, insecure=False, project_root=None)`**

Download and install a skill.

```python
import skilzy

# Basic installation
skilzy.install("skilzy-admin/pdf-pro")

# Install with custom options
skilzy.install(
    "skilzy-admin/pdf-pro",
    path="custom/path",
    overwrite=True,
    cat=True  # Print SKILL.md after install
)
```

**Parameters:**
- `skill_name` (str): Full skill name in format 'author/skill-name'
- `path` (str, optional): Custom installation path
- `overwrite` (bool): Replace existing installation if True
- `cat` (bool): Print SKILL.md content after installation
- `insecure` (bool): Disable SSL verification (use with caution)
- `project_root` (Path, optional): Project root directory

**Returns:** Dict with installation details

**Raises:**
- `ValueError`: Invalid skill name format
- `FileExistsError`: Directory exists and overwrite=False
- `SkilzyError`: API request failed

---

**`skilzy.list_skills(project_root=None)`**

List all installed skills tracked in `skilzy.json`.

```python
import skilzy

installed = skilzy.list_skills()
# Prints a formatted table and returns dict of skills
```

**Returns:** Dict of installed skills with metadata

---

**`skilzy.remove_skill(skill_name, force=False, project_root=None)`**

Remove a skill and update tracking file.

```python
import skilzy

# Interactive removal (prompts for confirmation)
skilzy.remove_skill("pdf-pro")

# Force removal (no confirmation)
skilzy.remove_skill("author/skill-name", force=True)
```

**Parameters:**
- `skill_name` (str): Name with or without author (e.g., 'pdf-pro' or 'author/pdf-pro')
- `force` (bool): Skip confirmation prompt if True

**Returns:** Dict with status message

---

**`skilzy.sync_skills(force=False, insecure=False, project_root=None)`**

Install all skills listed in `skilzy.json` (similar to `npm install`).

```python
import skilzy

# Sync all skills
result = skilzy.sync_skills()

# Force reinstall all skills
result = skilzy.sync_skills(force=True)

print(f"Synced: {result['success_count']}")
print(f"Skipped: {result['skip_count']}")
print(f"Errors: {result['error_count']}")
```

**Returns:** Dict with sync summary (success_count, skip_count, error_count)

---

#### **Authentication & Publishing**

**`skilzy.login(api_key)`**

Save your API key for authenticated operations.

```python
import skilzy

skilzy.login("sk_live_your_api_key_here")
```

**Returns:** Dict with status message

---

**`skilzy.publish(package_path, api_key=None)`**

Publish a new or updated skill to the registry.

```python
import skilzy

# Publish a packaged skill
response = skilzy.publish("dist/my-skill.zip")

print(f"Published: {response['skill']} v{response['version']}")
print(f"Status: {response['status']}")
```

**Returns:** Dict with publish response (skill, version, status)

**Raises:**
- `FileNotFoundError`: Package file not found
- `SkilzyAuthenticationError`: Not authenticated

---

**`skilzy.me_whoami()`**

Validate the currently configured API key.

```python
import skilzy

try:
    result = skilzy.me_whoami()
    print(f"Valid key: {result['key_prefix']}")
except skilzy.SkilzyAuthenticationError:
    print("Invalid API key")
```

**Returns:** Dict with validation status and key prefix

---

**`skilzy.me_skills(api_key=None)`**

List all skills you have published to the registry.

```python
import skilzy

my_skills = skilzy.me_skills()
# Prints a table and returns list of your skills
```

**Returns:** List of skill dictionaries with metadata

---

### Error Handling

The SDK uses specific exception types for different error scenarios:

```python
import skilzy

try:
    skilzy.install("invalid-skill-name")
except skilzy.SkilzyAuthenticationError:
    print("Authentication failed - run skilzy.login() first")
except skilzy.SkilzyNotFound:
    print("Skill not found in registry")
except skilzy.SkilzyError as e:
    print(f"API error: {e}")
except ValueError as e:
    print(f"Invalid input: {e}")
except FileExistsError as e:
    print(f"File conflict: {e}")
```

**Available Exception Classes:**
- `SkilzyError` - Base exception for all SDK errors
- `SkilzyAuthenticationError` - 401 authentication failures
- `SkilzyNotFound` - 404 resource not found
- `SkilzyPermissionError` - 403 forbidden
- `SkilzyConflictError` - 409 conflicts
- `SkilzyAPIError` - General API errors

---

## 🖥️ CLI Reference

### General Commands

**`skilzy init`**

Initialize a new `skilzy.json` tracking file in the current directory.

```bash
skilzy init
```

---

**`skilzy search <query>`**

Search for skills in the registry.

```bash
skilzy search "pdf"
skilzy search "automation" --author skilzy-admin
skilzy search "data" --keywords csv,excel
```

**Options:**
- `--author <name>` - Filter by author's username
- `--keywords <k1,k2>` - Comma-separated keywords

---

**`skilzy install <author/skill-name>`**

Download and install a skill into the local `./skills` directory.

```bash
skilzy install skilzy-admin/pdf-pro
skilzy install skilzy-admin/pdf-pro --overwrite
skilzy install skilzy-admin/pdf-pro --cat
skilzy install skilzy-admin/pdf-pro --path custom/location
```

**Options:**
- `--path <custom-path>` - Install to a specific directory
- `--overwrite` - Overwrite destination if it exists
- `--cat` - Print the skill's SKILL.md content after installation
- `--insecure` - Disable SSL certificate verification

---

**`skilzy list`**

List all skills currently installed in the local `./skills` directory.

```bash
skilzy list
```

---

**`skilzy remove <skill-name>`**

Remove a skill from the local installation.

```bash
skilzy remove pdf-pro
skilzy remove my-skill --force
```

**Options:**
- `--force` - Skip confirmation prompt

---

**`skilzy sync`**

Install all skills listed in `skilzy.json` (similar to `npm install`).

```bash
skilzy sync
skilzy sync --force
```

**Options:**
- `--force` - Reinstall all skills even if they exist
- `--insecure` - Disable SSL verification

---

### Publishing & Account Management

**`skilzy login`**

Securely save your API key for authenticated commands.

```bash
skilzy login
skilzy login --api-key "sk_live_your_key_here"
```

**Options:**
- `--api-key <key>` - Provide the API key directly (otherwise prompted)

---

**`skilzy publish <path/to/package.skill>`**

Publish a new or updated skill to the registry. Requires authentication.

```bash
skilzy publish dist/my-skill.zip
```

---

**`skilzy me whoami`**

Validate the currently configured API key.

```bash
skilzy me whoami
```

---

**`skilzy me skills`**

List all skills you have published, showing version and review status.

```bash
skilzy me skills
```

---

## 📖 Examples

### Example 1: Automated Skill Installation Script

```python
import skilzy

# Initialize tracking
skilzy.init()

# Install multiple skills
skills_to_install = [
    "skilzy-admin/pdf-pro",
    "skilzy-admin/web-scraper",
]

for skill in skills_to_install:
    try:
        result = skilzy.install(skill, overwrite=True)
        print(f"✓ Installed {result['skill']} v{result['version']}")
    except skilzy.SkilzyError as e:
        print(f"✗ Failed to install {skill}: {e}")

# List what was installed
print("
Installed skills:")
skilzy.list_skills()
```

### Example 2: Search and Interactive Install

```python
import skilzy

# Search for PDF-related skills
results = skilzy.search("pdf", limit=5)

if results:
    print("Available PDF skills:")
    for i, skill in enumerate(results, 1):
        print(f"{i}. {skill['author']}/{skill['name']} - {skill['description']}")
    
    choice = input("
Enter number to install (or 'q' to quit): ")
    if choice.isdigit():
        selected = results[int(choice) - 1]
        skill_name = f"{selected['author']}/{selected['name']}"
        skilzy.install(skill_name)
```

### Example 3: Sync Skills Across Environments

```python
import skilzy

# On machine 1: Install skills normally
skilzy.install("author/skill-1")
skilzy.install("author/skill-2")
# This creates skilzy.json with all dependencies

# Commit skilzy.json to version control

# On machine 2: Just sync
result = skilzy.sync_skills()
print(f"Synced {result['success_count']} skills successfully")
```

### Example 4: Publishing Workflow

```python
import skilzy

# Authenticate
skilzy.login("sk_live_your_api_key")

# Publish your skill
try:
    response = skilzy.publish("dist/my-awesome-skill.zip")
    print(f"✓ Published {response['skill']} v{response['version']}")
    print(f"  Status: {response['status']}")
except skilzy.SkilzyAuthenticationError:
    print("Authentication failed. Check your API key.")
except skilzy.SkilzyConflictError:
    print("This version already exists. Bump your version number.")

# Check your published skills
my_skills = skilzy.me_skills()
```

---

## 🔧 Advanced Usage

### Using the Low-Level Client

For more control, you can use the `SkilzyClient` class directly:

```python
from skilzy import SkilzyClient, SkilzyError

# Create client with custom settings
client = SkilzyClient(
    api_key="your_key",
    base_url="https://api.skilzy.dev",
    verify_ssl=True
)

try:
    # Search
    results = client.search_skills(q="automation", limit=10)
    
    # Get skill details
    details = client.get_skill_details(author="skilzy-admin", skill_name="pdf-pro")
    
    # Get specific version
    version = client.get_skill_version(
        author="skilzy-admin",
        skill_name="pdf-pro",
        version="1.0.0"
    )
    
    # Download
    client.download_skill(
        author="skilzy-admin",
        skill_name="pdf-pro",
        version="1.0.0",
        output_path="downloads/pdf-pro.skill"
    )
except SkilzyError as e:
    print(f"Error: {e}")
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Links

- **Homepage:** [https://github.com/skilzy-ai/skilzy-python](https://github.com/skilzy-ai/skilzy-python)
- **Issues:** [https://github.com/skilzy-ai/skilzy-python/issues](https://github.com/skilzy-ai/skilzy-python/issues)
- **PyPI:** [https://pypi.org/project/skilzy/](https://pypi.org/project/skilzy/)
- **Registry:** [https://skilzy.ai](https://skilzy.ai)

---

## 💡 Need Help?

- 📖 Check the [documentation](https://docs.skilzy.ai)
- 🐛 Report bugs on [GitHub Issues](https://github.com/skilzy-ai/skilzy-python/issues)
