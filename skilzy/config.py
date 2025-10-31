# skilzy/config.py
import configparser
from pathlib import Path

# Configuration paths and constants
CONFIG_DIR = Path.home() / ".skilzy"
CONFIG_FILE = CONFIG_DIR / "config.ini"
CONFIG_SECTION = "auth"
CONFIG_KEY_FIELD = "api_key"

def save_api_key(api_key: str):
    """Saves the API key to the config file, creating it if necessary."""
    try:
        # Ensure the config directory exists
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        
        config = configparser.ConfigParser()
        config[CONFIG_SECTION] = {CONFIG_KEY_FIELD: api_key}
        
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
        
        # Restrict file permissions for security - only user can read/write
        CONFIG_FILE.chmod(0o600)
    except Exception as e:
        # Provide context for upstream error handling
        raise IOError(f"Failed to save configuration to {CONFIG_FILE}: {e}")

def load_api_key() -> str | None:
    """Loads the API key from the config file."""
    if not CONFIG_FILE.exists():
        return None
    
    try:
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)
        return config.get(CONFIG_SECTION, CONFIG_KEY_FIELD, fallback=None)
    except (configparser.Error, IOError):
        # Return None for any configuration errors to allow graceful handling
        return None