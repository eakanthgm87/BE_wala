# deployment/__init__.py
from .deployment_manager import DeploymentManager  # noqa: F401

try:
    from .ai_commands import handle_command        # noqa: F401
except ImportError:
    def handle_command(raw_input: str) -> bool:
        print("[WARN] ai_commands.py missing from deployment folder.")
        return False

__all__ = ["handle_command", "DeploymentManager"]
