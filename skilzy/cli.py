# skilzy/cli.py

import typer
from typing import Optional
from pathlib import Path
from typing_extensions import Annotated

# Import the core action functions
from . import actions
from .errors import SkilzyError, SkilzyAuthenticationError

# ===============================================
# Main App and Command Groups
# ===============================================

app = typer.Typer(
    name="skilzy",
    help="A CLI for discovering, installing, and managing AI skills from the Skilzy Registry."
)

me_app = typer.Typer(
    name="me",
    help="Manage your Skilzy account and published skills."
)
app.add_typer(me_app)

# ===============================================
# Core Commands
# ===============================================

@app.command()
def login(
    api_key: Annotated[Optional[str], typer.Option("--api-key", help="Your Skilzy API key. If not provided, you will be prompted.")] = None
):
    """
    Authenticate with the Skilzy Registry by saving your API key.
    """
    if not api_key:
        api_key = typer.prompt("Please enter your Skilzy API key", hide_input=True)
    
    try:
        actions.login(api_key)
    except ValueError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    except IOError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

@app.command()
def publish(
    package_path: Annotated[Path, typer.Argument(help="Path to the packaged .skill file to publish.")]
):
    """
    Publish a new or updated skill to the Skilzy Registry.
    Requires authentication via 'skilzy login'.
    """
    try:
        actions.publish(str(package_path))
    except FileNotFoundError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    except SkilzyAuthenticationError as e:
        typer.secho(f"\nError: {e}", fg=typer.colors.RED)
        typer.secho("Please run 'skilzy login' first.", fg=typer.colors.YELLOW)
        raise typer.Exit(code=1)
    except SkilzyError as e:
        typer.secho(f"\nError: Failed to publish skill: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.secho(f"\nAn unexpected error occurred: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

@app.command()
def init():
    """
    Initialize a new skilzy.json tracking file in the current directory.
    """
    try:
        result = actions.init()
        if result["status"] == "created":
            typer.secho(f"Successfully created '{result['path']}'.", fg=typer.colors.GREEN)
        else:
            typer.secho(f"'{result['path']}' already exists.", fg=typer.colors.YELLOW)
    except Exception as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

@app.command()
def search(
    query: Annotated[str, typer.Argument(help="The search query for skills.")],
    author: Annotated[Optional[str], typer.Option("--author", help="Filter by author's username.")] = None,
    keywords: Annotated[Optional[str], typer.Option("--keywords", help="Comma-separated keywords to filter by.")] = None,
):
    """
    Search for skills in the Skilzy Registry.
    """
    try:
        keywords_list = keywords.split(',') if keywords else None
        actions.search(query=query, author=author, keywords=keywords_list)
    except SkilzyError as e:
        typer.secho(f"API Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.secho(f"An unexpected error occurred: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

@app.command()
def install(
    skill_name: Annotated[str, typer.Argument(help="The full name of the skill, e.g., 'author/skill-name'.")],
    path: Annotated[Optional[Path], typer.Option("--path", help="Custom installation path. Overrides the default ./skills/<skill-name> location.")] = None,
    overwrite: Annotated[bool, typer.Option("--overwrite", help="Overwrite the destination directory if it already exists.")] = False,
    cat: Annotated[bool, typer.Option("--cat", help="Print the skill's SKILL.md file content to the console after installation.")] = False,
    insecure: Annotated[bool, typer.Option("--insecure", help="Disable SSL certificate verification. Use with caution.")] = False,
):
    """
    Download and install a skill, creating a tracking file if needed.
    """
    try:
        actions.install(
            skill_name=skill_name,
            path=str(path) if path else None,
            overwrite=overwrite,
            cat=cat,
            insecure=insecure
        )
    except ValueError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    except FileExistsError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        typer.secho("Use --overwrite to replace it or --path to specify a different location.", fg=typer.colors.YELLOW)
        raise typer.Exit(code=1)
    except SkilzyError as e:
        typer.secho(f"API Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.secho(f"An unexpected error occurred: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

@app.command("list")
def list_skills():
    """
    List all skills tracked in the local skilzy.json file.
    """
    try:
        actions.list_skills()
    except FileNotFoundError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.YELLOW)
        raise typer.Exit()
    except Exception as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

@app.command("remove")
def remove_skill(
    skill_name: Annotated[str, typer.Argument(help="The name of the skill to remove (e.g., 'pdf-pro').")],
    force: Annotated[bool, typer.Option("--force", help="Force removal without a confirmation prompt.")] = False,
):
    """
    Remove a skill and update the skilzy.json tracking file.
    """
    try:
        result = actions.remove_skill(skill_name, force=force)
        if result["status"] == "cancelled":
            typer.echo("Removal cancelled.")
            raise typer.Exit()
    except ValueError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.secho(f"Error: Failed to remove skill: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

@app.command("sync")
def sync_skills(
    force: Annotated[bool, typer.Option("--force", help="Reinstall all skills even if they already exist.")] = False,
    insecure: Annotated[bool, typer.Option("--insecure", help="Disable SSL certificate verification. Use with caution.")] = False,
):
    """
    Install all skills listed in skilzy.json (similar to 'npm install').
    """
    try:
        result = actions.sync_skills(force=force, insecure=insecure)
        if result["error_count"] > 0:
            raise typer.Exit(code=1)
    except FileNotFoundError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

# ===============================================
# "me" Subcommand
# ===============================================

@me_app.command("whoami")
def me_whoami():
    """
    Validates the currently configured API key and shows its prefix.
    """
    try:
        actions.me_whoami()
    except ValueError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        typer.secho("Please run 'skilzy login' first.", fg=typer.colors.YELLOW)
        raise typer.Exit(code=1)
    except SkilzyAuthenticationError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        typer.secho("Please verify this key is correct on your backend or re-run 'skilzy login'.", fg=typer.colors.YELLOW)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.secho(f"An unexpected error occurred during validation: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

@me_app.command("skills")
def me_skills():
    """
    List all skills you have published to the registry.
    """
    try:
        actions.me_skills()
    except SkilzyAuthenticationError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    except SkilzyError as e:
        typer.secho(f"API Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

# This is the entrypoint for the CLI
if __name__ == "__main__":
    app()
