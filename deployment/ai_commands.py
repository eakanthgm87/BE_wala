"""
ai_commands.py
───────────────────────────────────────────────────────────────────────────────
One-click command dispatcher.

Plug one line into your terminal / chat loop:

    from deployment import handle_command
    if not handle_command(user_input):
        # not an ai: command — handle normally

All supported commands
──────────────────────
  ai:deploy                    Docker deploy of current directory
  ai:deploy /path              Docker deploy of a specific folder
  ai:deploy --registry USER    Deploy + push image to Docker Hub
  ai:deploy --name myapp       Custom image / service name
  ai:deploy --no-overwrite     Keep existing Dockerfile

  ai:deploy kubernetes         Kubernetes deploy (current directory)
  ai:deploy kubernetes /path   Kubernetes deploy of a specific folder
  ai:deploy kubernetes --registry USER --replicas 3

  ai:destroy                   Stop Docker containers + remove image
  ai:destroy --target docker       (same as above)
  ai:destroy --target kubernetes   Delete K8s namespace + image
  ai:destroy --target all          Both Docker and K8s
  ai:destroy --name myapp          Specify image / namespace name

  ai:status                    docker compose ps
  ai:logs                      docker compose logs -f  (Ctrl-C to stop)
  ai:help                      Print this help
"""

from __future__ import annotations

import shlex
import subprocess
import sys
from pathlib import Path

from .ai_deploy_runner import run_deploy_docker, run_deploy_k8s, run_destroy


# ─── tiny arg parser ─────────────────────────────────────────────────────────

def _parse(tokens: list[str]) -> dict:
    a = {"path": ".", "registry": None, "name": None,
         "overwrite": True, "replicas": 2, "target": "docker"}
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t in ("--registry","-r") and i+1 < len(tokens):
            a["registry"] = tokens[i+1]; i += 2
        elif t in ("--name","-n") and i+1 < len(tokens):
            a["name"] = tokens[i+1]; i += 2
        elif t in ("--replicas",) and i+1 < len(tokens):
            try: a["replicas"] = int(tokens[i+1])
            except ValueError: pass
            i += 2
        elif t in ("--target","-t") and i+1 < len(tokens):
            a["target"] = tokens[i+1]; i += 2
        elif t == "--no-overwrite":
            a["overwrite"] = False; i += 1
        elif not t.startswith("-"):
            a["path"] = t; i += 1
        else:
            i += 1
    return a


# ─── command handlers ─────────────────────────────────────────────────────────

def _cmd_deploy(tokens: list[str]) -> int:
    # Check if first token is a sub-target keyword
    sub = tokens[0].lower() if tokens else ""
    if sub in ("kubernetes","k8s","kube"):
        return _cmd_deploy_k8s(tokens[1:])
    if sub in ("docker","compose"):
        tokens = tokens[1:]
    return _cmd_deploy_docker(tokens)

def _cmd_deploy_docker(tokens: list[str]) -> int:
    a = _parse(tokens)
    return run_deploy_docker(
        project_path=a["path"],
        image_name=a["name"],
        registry=a["registry"],
        overwrite_dockerfile=a["overwrite"],
    )

def _cmd_deploy_k8s(tokens: list[str]) -> int:
    a = _parse(tokens)
    return run_deploy_k8s(
        project_path=a["path"],
        image_name=a["name"],
        registry=a["registry"],
        replicas=a["replicas"],
        overwrite_dockerfile=a["overwrite"],
    )

def _cmd_destroy(tokens: list[str]) -> int:
    a = _parse(tokens)
    return run_destroy(
        project_path=a["path"],
        image_name=a["name"],
        target=a["target"],
    )

def _cmd_status(tokens: list[str]) -> int:
    a    = _parse(tokens)
    path = Path(a["path"]).resolve()
    print("\n  Running containers:\n")
    r = subprocess.run(["docker","compose","ps"], cwd=path, text=True)
    if r.returncode != 0:
        subprocess.run(["docker-compose","ps"], cwd=path)
    return 0

def _cmd_logs(tokens: list[str]) -> int:
    a    = _parse(tokens)
    path = Path(a["path"]).resolve()
    try:
        subprocess.run(["docker","compose","logs","-f","--tail=50"], cwd=path)
    except KeyboardInterrupt:
        pass
    return 0

_HELP = """
  ┌────────────────────────────────────────────────────────────────┐
  │                    ai:deploy  commands                         │
  ├────────────────────────────────────────────────────────────────┤
  │                                                                │
  │  DOCKER (default)                                              │
  │    ai:deploy                   deploy current folder          │
  │    ai:deploy /path             deploy a specific folder       │
  │    ai:deploy --registry USER   deploy + push to Docker Hub    │
  │    ai:deploy --name myapp      custom image name              │
  │    ai:deploy --no-overwrite    keep existing Dockerfile       │
  │                                                                │
  │  KUBERNETES                                                    │
  │    ai:deploy kubernetes        k8s deploy current folder      │
  │    ai:deploy kubernetes /path  k8s deploy specific folder     │
  │    ai:deploy kubernetes --registry USER --replicas 3          │
  │                                                                │
  │  DESTROY                                                       │
  │    ai:destroy                       stop docker containers    │
  │    ai:destroy --target kubernetes   delete k8s namespace      │
  │    ai:destroy --target all          nuke both                 │
  │    ai:destroy --name myapp          specify name              │
  │                                                                │
  │  OTHER                                                         │
  │    ai:status    show running containers                       │
  │    ai:logs      tail compose logs  (Ctrl-C to stop)           │
  │    ai:help      show this help                                │
  └────────────────────────────────────────────────────────────────┘
"""

def _cmd_help(_tokens: list[str]) -> int:
    print(_HELP); return 0


# ─── registry ────────────────────────────────────────────────────────────────

_COMMANDS: dict[str, object] = {
    "ai:deploy":  _cmd_deploy,
    "ai:destroy": _cmd_destroy,
    "ai:status":  _cmd_status,
    "ai:logs":    _cmd_logs,
    "ai:help":    _cmd_help,
}

_ALIASES: dict[str, str] = {
    "deploy":  "ai:deploy",
    "destroy": "ai:destroy",
    "status":  "ai:status",
    "logs":    "ai:logs",
    "help":    "ai:help",
}


# ─── public entry-point ───────────────────────────────────────────────────────

def handle_command(raw_input: str) -> bool:
    """
    Route raw_input to the matching ai: command.

    Returns True  if the input was an ai: command (handled).
    Returns False if it was not recognised (caller should handle it).

    Usage
    -----
    >>> handle_command("ai:deploy")
    >>> handle_command("ai:deploy kubernetes --registry myuser --replicas 3")
    >>> handle_command("ai:destroy --target all")
    """
    raw = raw_input.strip()
    if not raw:
        return False

    try:
        tokens = shlex.split(raw)
    except ValueError:
        tokens = raw.split()

    if not tokens:
        return False

    cmd = tokens[0].lower()
    if cmd in _ALIASES:
        cmd = _ALIASES[cmd]

    if cmd not in _COMMANDS:
        return False

    try:
        _COMMANDS[cmd](tokens[1:])   # type: ignore[operator]
    except KeyboardInterrupt:
        print("\n  Interrupted.")
    except Exception as exc:
        print(f"\n  [ERROR] {cmd} crashed: {exc}")
        import traceback; traceback.print_exc()

    return True


# ─── allow  python -m deployment.ai_commands  ai:deploy ──────────────────────
if __name__ == "__main__":
    raw = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "ai:help"
    handle_command(raw)
