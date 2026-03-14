"""
dockerfile_generator.py
────────────────────────
Thin wrapper kept for backward compatibility.
All real logic now lives in ai_deploy_runner.py so both the CLI and
DeploymentManager always generate identical Dockerfiles.
"""

from pathlib import Path
from .ai_deploy_runner import detect_framework, generate_dockerfile as _gen


class DockerfileGenerator:
    """Generates optimized Dockerfiles based on project type."""

    # ── Main public method (called by DeploymentManager) ─────────────────────

    def generate_dockerfile(self, project_info: dict, output_path: str = ".") -> str:
        """
        Detect the project language, generate the correct Dockerfile,
        write it to output_path/Dockerfile, and return the file path.
        """
        path = Path(output_path).resolve()
        framework, profile = detect_framework(path)

        # Allow project_info to override the detected framework
        override = project_info.get("framework", "").lower()
        if override and override not in ("unknown", ""):
            from .ai_deploy_runner import PROFILES
            if override in PROFILES:
                framework = override
                profile   = PROFILES[override]

        df = _gen(path, framework, profile)
        print(f"   [Dockerfile] {framework}  port={profile['port']}  → {df}")
        return str(df)

    # ── generate_optimized_dockerfile (used by docker_manager) ───────────────

    def generate_optimized_dockerfile(self, service_config: dict,
                                       project_path: str | None = None) -> str:
        """Return Dockerfile content as a string (does not write to disk)."""
        from .ai_deploy_runner import PROFILES, _find_entry, _resolve_cmd

        fw      = service_config.get("framework", "python").lower()
        profile = PROFILES.get(fw, PROFILES["python"])
        port    = service_config.get("port") or profile["port"]

        # Override port in a copy so we don't mutate the global profile
        p = {**profile, "port": port}

        path = Path(project_path) if project_path else Path(".")
        entry = _find_entry(path, p)
        cmd   = _resolve_cmd(p, entry)

        dep     = p.get("dep_copy", "")
        install = p.get("install",  "")
        build   = p.get("build",    "")

        if "runtime_image" in p:
            return (
                f"# ai:deploy  framework: {fw}\n"
                f"FROM {p['base_image']} AS builder\n"
                f"WORKDIR /app\n"
                f"{dep}\n{install}\n"
                f"COPY . .\n{build}\n\n"
                f"FROM {p['runtime_image']}\n"
                f"WORKDIR /app\n"
                f"{p.get('runtime_copy','COPY --from=builder /app /app')}\n"
                f"EXPOSE {port}\nCMD {cmd}\n"
            )

        return (
            f"# ai:deploy  framework: {fw}\n"
            f"FROM {p['base_image']}\n"
            f"WORKDIR /app\n"
            f"{dep}\n{install}\n"
            f"COPY . .\n{build}\n"
            f"EXPOSE {port}\nCMD {cmd}\n"
        )

    # ── Legacy shim methods ───────────────────────────────────────────────────

    def select_template(self, service_config: dict) -> dict:
        from .ai_deploy_runner import PROFILES
        fw = service_config.get("framework", "python").lower()
        p  = PROFILES.get(fw, PROFILES["python"])
        return {
            "base_image":    p["base_image"],
            "runtime_image": p.get("runtime_image", p["base_image"]),
            "install_cmd":   p.get("install",""),
            "run_cmd":       p.get("cmd",""),
        }

    def copy_dependency_files(self, service_config: dict) -> str:
        from .ai_deploy_runner import PROFILES
        fw = service_config.get("framework","python").lower()
        return PROFILES.get(fw, PROFILES["python"]).get("dep_copy","COPY . .")

    def get_install_command(self, service_config: dict) -> str:
        return self.select_template(service_config)["install_cmd"]

    def get_build_command(self, service_config: dict) -> str:
        from .ai_deploy_runner import PROFILES
        fw = service_config.get("framework","python").lower()
        return PROFILES.get(fw, PROFILES["python"]).get("build","")

    def get_run_command(self, service_config: dict) -> str:
        return f"CMD {self.select_template(service_config)['run_cmd']}"

    def get_optimizations(self, _service_config: dict) -> list:
        return []

    def _simple_python_dockerfile(self, script_name: str) -> str:
        return (
            f"FROM python:3.11-slim\n"
            f"WORKDIR /app\n"
            f"COPY . .\n"
            f"RUN pip install --no-cache-dir -r requirements.txt 2>/dev/null || true\n"
            f'CMD ["python", "{script_name}"]\n'
        )

    # keep old names so nothing breaks
    def _fastapi_dockerfile(self):   return self.generate_optimized_dockerfile({"framework":"fastapi","port":8000})
    def _flask_dockerfile(self):     return self.generate_optimized_dockerfile({"framework":"flask",  "port":5000})
    def _django_dockerfile(self):    return self.generate_optimized_dockerfile({"framework":"django",  "port":8000})
    def _nodejs_dockerfile(self):    return self.generate_optimized_dockerfile({"framework":"nodejs",  "port":3000})
    def _get_dockerfile_content(self, fw, _info):
        return self.generate_optimized_dockerfile({"framework": fw.lower(), "port": 8000})
