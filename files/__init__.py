# deployment/__init__.py
"""
AI Deploy — language-independent one-click deployment module.

Quick start
-----------
    from deployment import handle_command

    # In your terminal / chat loop:
    handle_command("ai:deploy")                          # Docker deploy cwd
    handle_command("ai:deploy kubernetes")               # K8s deploy cwd
    handle_command("ai:deploy --registry myuser")        # Docker + push
    handle_command("ai:deploy kubernetes --registry myuser --replicas 3")
    handle_command("ai:destroy")                         # stop + clean Docker
    handle_command("ai:destroy --target kubernetes")     # delete K8s namespace
    handle_command("ai:destroy --target all")            # nuke everything
    handle_command("ai:help")                            # show all commands
"""

from .ai_commands import handle_command                        # noqa: F401
from .ai_deploy_runner import (                                # noqa: F401
    run_deploy_docker,
    run_deploy_k8s,
    run_destroy,
    detect_framework,
    generate_dockerfile,
    PROFILES,
)
from .deployment_manager import DeploymentManager              # noqa: F401

__all__ = [
    "handle_command",
    "run_deploy_docker",
    "run_deploy_k8s",
    "run_destroy",
    "detect_framework",
    "generate_dockerfile",
    "PROFILES",
    "DeploymentManager",
]
