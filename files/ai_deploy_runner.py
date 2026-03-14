"""
ai_deploy_runner.py
───────────────────────────────────────────────────────────────────────────────
Language-independent one-click deploy engine.

Auto-detects and supports:
  Python   → FastAPI, Flask, Django, Streamlit, generic
  Node.js  → React, Next.js, Express, generic Node
  Go       → go.mod
  Rust     → Cargo.toml
  Java     → Maven (pom.xml) / Gradle (build.gradle)
  Ruby     → Gemfile / Rails
  PHP      → composer.json
  .NET     → *.csproj / *.fsproj
  Static   → HTML/CSS/JS only

Deployment targets:
  run_deploy_docker(path, image, registry)   Dockerfile + compose + up
  run_deploy_k8s(path, image, registry)      Dockerfile + k8s manifests + apply
  run_destroy(path, image, target)           compose down / kubectl delete + rmi
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path


# ─── colours ──────────────────────────────────────────────────────────────────

_TTY = sys.stdout.isatty()

def _c(code: str, text: str) -> str:
    _m = {"bold":"1","green":"92","yellow":"93","red":"91","cyan":"96","dim":"2","blue":"94"}
    return f"\033[{_m[code]}m{text}\033[0m" if _TTY else text

def _banner(t: str):
    w = 64
    print("\n" + _c("bold","╔"+"═"*w+"╗"))
    p = (w-len(t))//2
    print(_c("bold","║")+" "*p+_c("cyan",_c("bold",t))+" "*(w-p-len(t))+_c("bold","║"))
    print(_c("bold","╚"+"═"*w+"╝"))

def _step(n,tot,msg): print(f"\n  {_c('bold',_c('cyan',f'[{n}/{tot}]'))}  {msg}")
def _ok(m):   print(f"        {_c('green','✔')}  {m}")
def _warn(m): print(f"        {_c('yellow','⚠')}  {m}")
def _fail(m): print(f"        {_c('red','✘')}  {m}", file=sys.stderr)
def _info(m): print(f"        {_c('dim','→')}  {m}")


# ─── language / framework profiles ───────────────────────────────────────────
#
# Required keys: port, base_image, dep_copy, install, cmd
# Optional:      build, runtime_image, runtime_copy, health_path, entry_detect
# {entry} and {entry_module} in cmd are replaced at runtime

PROFILES: dict[str, dict] = {
    # Python
    "fastapi": {
        "port":8000, "base_image":"python:3.11-slim",
        "dep_copy":"COPY requirements.txt* ./",
        "install":"RUN pip install --no-cache-dir -r requirements.txt",
        "cmd":'["uvicorn", "{entry_module}:app", "--host", "0.0.0.0", "--port", "8000"]',
        "entry_detect":["main.py","app.py","server.py","api.py","asgi.py"],
        "health_path":"/health",
    },
    "flask": {
        "port":5000, "base_image":"python:3.11-slim",
        "dep_copy":"COPY requirements.txt* ./",
        "install":"RUN pip install --no-cache-dir -r requirements.txt",
        "cmd":'["python", "{entry}"]',
        "entry_detect":["app.py","run.py","main.py","wsgi.py","server.py"],
        "health_path":"/",
    },
    "django": {
        "port":8000, "base_image":"python:3.11-slim",
        "dep_copy":"COPY requirements.txt* ./",
        "install":"RUN pip install --no-cache-dir -r requirements.txt",
        "cmd":'["python", "manage.py", "runserver", "0.0.0.0:8000"]',
        "health_path":"/",
    },
    "streamlit": {
        "port":8501, "base_image":"python:3.11-slim",
        "dep_copy":"COPY requirements.txt* ./",
        "install":"RUN pip install --no-cache-dir -r requirements.txt",
        "cmd":'["streamlit","run","{entry}","--server.port=8501","--server.address=0.0.0.0"]',
        "entry_detect":["app.py","main.py","streamlit_app.py"],
        "health_path":"/_stcore/health",
    },
    "python": {
        "port":8000, "base_image":"python:3.11-slim",
        "dep_copy":"COPY requirements.txt* ./",
        "install":"RUN pip install --no-cache-dir -r requirements.txt 2>/dev/null || true",
        "cmd":'["python", "{entry}"]',
        "entry_detect":["main.py","app.py","run.py","server.py","index.py","start.py"],
        "health_path":"/",
    },
    # Node
    "nextjs": {
        "port":3000, "base_image":"node:20-alpine",
        "dep_copy":"COPY package*.json ./",
        "install":"RUN npm ci",
        "build":"RUN npm run build",
        "cmd":'["npm","start"]',
        "health_path":"/",
    },
    "react": {
        "port":80, "base_image":"node:20-alpine",
        "dep_copy":"COPY package*.json ./",
        "install":"RUN npm ci",
        "build":"RUN npm run build",
        "runtime_image":"nginx:alpine",
        "runtime_copy":"COPY --from=builder /app/build /usr/share/nginx/html",
        "cmd":'["nginx","-g","daemon off;"]',
        "health_path":"/",
    },
    "nodejs": {
        "port":3000, "base_image":"node:20-alpine",
        "dep_copy":"COPY package*.json ./",
        "install":"RUN npm ci --omit=dev",
        "cmd":'["node","{entry}"]',
        "entry_detect":["index.js","server.js","app.js","main.js","src/index.js"],
        "health_path":"/",
    },
    # Go
    "go": {
        "port":8080, "base_image":"golang:1.22-alpine",
        "dep_copy":"COPY go.mod go.sum* ./",
        "install":"RUN go mod download",
        "build":"RUN go build -o /app/server .",
        "runtime_image":"alpine:3.19",
        "runtime_copy":"COPY --from=builder /app/server /app/server",
        "cmd":'["/app/server"]',
        "health_path":"/health",
    },
    # Rust
    "rust": {
        "port":8080, "base_image":"rust:1.77-slim",
        "dep_copy":"COPY Cargo.toml Cargo.lock* ./",
        "install":"RUN mkdir src && echo 'fn main(){}' > src/main.rs && cargo build --release && rm -rf src",
        "build":"RUN cargo build --release",
        "runtime_image":"debian:bookworm-slim",
        "runtime_copy":"COPY --from=builder /app/target/release/app /app/server",
        "cmd":'["/app/server"]',
        "health_path":"/health",
    },
    # Java Maven
    "java-maven": {
        "port":8080, "base_image":"maven:3.9-eclipse-temurin-21",
        "dep_copy":"COPY pom.xml ./",
        "install":"RUN mvn dependency:go-offline -q",
        "build":"RUN mvn package -DskipTests -q",
        "runtime_image":"eclipse-temurin:21-jre-alpine",
        "runtime_copy":"COPY --from=builder /app/target/*.jar /app/app.jar",
        "cmd":'["java","-jar","/app/app.jar"]',
        "health_path":"/actuator/health",
    },
    # Java Gradle
    "java-gradle": {
        "port":8080, "base_image":"gradle:8-jdk21",
        "dep_copy":"COPY build.gradle* settings.gradle* gradlew* ./\nCOPY gradle gradle/",
        "install":"RUN ./gradlew dependencies --no-daemon -q 2>/dev/null || true",
        "build":"RUN ./gradlew bootJar --no-daemon -q",
        "runtime_image":"eclipse-temurin:21-jre-alpine",
        "runtime_copy":"COPY --from=builder /app/build/libs/*.jar /app/app.jar",
        "cmd":'["java","-jar","/app/app.jar"]',
        "health_path":"/actuator/health",
    },
    # Ruby
    "rails": {
        "port":3000, "base_image":"ruby:3.3-slim",
        "dep_copy":"COPY Gemfile Gemfile.lock* ./",
        "install":"RUN bundle install --without development test",
        "build":"RUN bundle exec rake assets:precompile 2>/dev/null || true",
        "cmd":'["bundle","exec","rails","server","-b","0.0.0.0"]',
        "health_path":"/",
    },
    "ruby": {
        "port":3000, "base_image":"ruby:3.3-slim",
        "dep_copy":"COPY Gemfile Gemfile.lock* ./",
        "install":"RUN bundle install --without development test",
        "cmd":'["ruby","{entry}"]',
        "entry_detect":["app.rb","server.rb","main.rb","config.ru"],
        "health_path":"/",
    },
    # PHP
    "php": {
        "port":80, "base_image":"php:8.3-apache",
        "dep_copy":"COPY composer.json composer.lock* ./",
        "install":(
            "RUN curl -sS https://getcomposer.org/installer | php -- "
            "--install-dir=/usr/local/bin --filename=composer && "
            "composer install --no-dev --optimize-autoloader 2>/dev/null || true"
        ),
        "cmd":'["apache2-foreground"]',
        "health_path":"/",
    },
    # .NET
    "dotnet": {
        "port":8080, "base_image":"mcr.microsoft.com/dotnet/sdk:8.0",
        "dep_copy":"COPY *.csproj ./",
        "install":"RUN dotnet restore",
        "build":"RUN dotnet publish -c Release -o /app/publish",
        "runtime_image":"mcr.microsoft.com/dotnet/aspnet:8.0",
        "runtime_copy":"COPY --from=builder /app/publish /app",
        "cmd":'["dotnet","app.dll"]',
        "health_path":"/health",
    },
    # Static HTML
    "static": {
        "port":80, "base_image":"nginx:alpine",
        "dep_copy":"",
        "install":"",
        "cmd":'["nginx","-g","daemon off;"]',
        "health_path":"/",
    },
}


# ─── detection ────────────────────────────────────────────────────────────────

def detect_framework(path: Path) -> tuple[str, dict]:
    files = {f.name.lower() for f in path.iterdir() if f.is_file()}

    # .NET
    if any(f.endswith(".csproj") or f.endswith(".fsproj") for f in files):
        return "dotnet", PROFILES["dotnet"]
    # Java
    if "pom.xml" in files:
        return "java-maven", PROFILES["java-maven"]
    if "build.gradle" in files or "build.gradle.kts" in files:
        return "java-gradle", PROFILES["java-gradle"]
    # Go
    if "go.mod" in files:
        return "go", PROFILES["go"]
    # Rust
    if "cargo.toml" in files:
        return "rust", PROFILES["rust"]
    # Ruby
    if "gemfile" in files:
        txt = (path/"Gemfile").read_text(errors="ignore").lower()
        return ("rails" if "rails" in txt else "ruby"), PROFILES["rails" if "rails" in txt else "ruby"]
    # PHP
    if "composer.json" in files or any(f.endswith(".php") for f in files):
        return "php", PROFILES["php"]
    # Node
    if "package.json" in files:
        try:
            pkg  = json.loads((path/"package.json").read_text())
            deps = {**pkg.get("dependencies",{}), **pkg.get("devDependencies",{})}
            if "next" in deps:  return "nextjs", PROFILES["nextjs"]
            if "react" in deps: return "react",  PROFILES["react"]
        except Exception:
            pass
        return "nodejs", PROFILES["nodejs"]
    # Python
    reqs = ""
    if "requirements.txt" in files:
        reqs += (path/"requirements.txt").read_text(errors="ignore").lower()
    if "pyproject.toml" in files:
        reqs += (path/"pyproject.toml").read_text(errors="ignore").lower()
    if reqs or "setup.py" in files:
        for fw in ("fastapi","uvicorn","django","streamlit","flask"):
            if fw in reqs:
                mapped = {"uvicorn":"fastapi"}.get(fw, fw)
                return mapped, PROFILES[mapped]
        return "python", PROFILES["python"]
    if any(f.endswith(".py") for f in files):
        return "python", PROFILES["python"]
    # Static
    if "index.html" in files or any(f.endswith(".html") for f in files):
        return "static", PROFILES["static"]
    return "python", PROFILES["python"]


def _find_entry(path: Path, profile: dict) -> str:
    for c in profile.get("entry_detect", []):
        if (path/c).exists(): return c
    py = sorted(path.glob("*.py"))
    return py[0].name if py else "main.py"

def _resolve_cmd(profile: dict, entry: str) -> str:
    mod = entry.replace(".py","").replace("/",".").replace("\\",".")
    return profile["cmd"].replace("{entry}", entry).replace("{entry_module}", mod)


# ─── Dockerfile ───────────────────────────────────────────────────────────────

def generate_dockerfile(path: Path, framework: str, profile: dict) -> Path:
    port    = profile["port"]
    health  = profile.get("health_path", "/")
    entry   = _find_entry(path, profile)
    cmd     = _resolve_cmd(profile, entry)
    dep     = profile.get("dep_copy", "")
    install = profile.get("install", "")
    build   = profile.get("build", "")

    header = (
        f"# Auto-generated by ai:deploy  |  language: {framework}\n"
        f"# Entry: {entry}   Port: {port}\n"
    )

    if "runtime_image" in profile:
        body = (
            f"{header}\n"
            f"# ── Stage 1: build ─────────────────────────────────────\n"
            f"FROM {profile['base_image']} AS builder\n"
            f"WORKDIR /app\n\n"
            f"{dep}\n"
            f"{install}\n\n"
            f"COPY . .\n"
            f"{build}\n\n"
            f"# ── Stage 2: runtime ────────────────────────────────────\n"
            f"FROM {profile['runtime_image']}\n"
            f"WORKDIR /app\n"
            f"{profile.get('runtime_copy','COPY --from=builder /app /app')}\n\n"
            f"EXPOSE {port}\n"
            f"CMD {cmd}\n"
        )
    else:
        nonroot = ""
        if any(x in profile["base_image"] for x in ("alpine","slim","debian","ubuntu")):
            nonroot = (
                "\n# Non-root user for security\n"
                "RUN addgroup --system appgroup && "
                "adduser --system --ingroup appgroup appuser 2>/dev/null || true\n"
                "USER appuser\n"
            )
        hc = (
            f"\nHEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \\\n"
            f"    CMD wget -qO- http://localhost:{port}{health} 2>/dev/null || exit 0\n"
        ) if health else ""

        body = (
            f"{header}\n"
            f"FROM {profile['base_image']}\n"
            f"WORKDIR /app\n\n"
            f"# Dependencies first (layer-cache friendly)\n"
            f"{dep}\n"
            f"{install}\n\n"
            f"# Full source\n"
            f"COPY . .\n"
            f"{build}\n"
            f"{nonroot}"
            f"{hc}\n"
            f"EXPOSE {port}\n"
            f"CMD {cmd}\n"
        )

    df = path / "Dockerfile"
    df.write_text(body)
    return df


# ─── docker helpers ───────────────────────────────────────────────────────────

def _safe_name(s: str) -> str:
    return re.sub(r"[^a-z0-9_-]","-",s.lower()).strip("-") or "myapp"

def _docker_ok() -> bool:
    return subprocess.run(["docker","info"],capture_output=True).returncode == 0

def _kubectl_ok() -> bool:
    return subprocess.run(["kubectl","version","--client"],capture_output=True).returncode == 0

def _compose_exe() -> list[str]:
    r = subprocess.run(["docker","compose","version"],capture_output=True)
    return ["docker","compose"] if r.returncode==0 else ["docker-compose"]

def _dotenv(path: Path) -> dict[str,str]:
    env: dict[str,str] = {}
    for n in [".env",".env.local",".env.production"]:
        p = path/n
        if p.exists():
            for line in p.read_text(errors="ignore").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k,_,v = line.partition("=")
                    env.setdefault(k.strip(), v.strip())
    return env

def _run(cmd: list[str], cwd=None, env=None) -> bool:
    _info(" ".join(str(c) for c in cmd))
    r = subprocess.run(cmd, cwd=cwd, env={**os.environ,**(env or {})})
    return r.returncode == 0

def build_image(path: Path, tag: str) -> bool:
    return _run(["docker","build","-t",tag,"."], cwd=path, env={"DOCKER_BUILDKIT":"1"})

def push_image(local: str, registry: str) -> tuple[bool,str]:
    remote = f"{registry}/{local.split(':')[0]}:latest"
    if not _run(["docker","tag",local,remote]): return False,remote
    ok = _run(["docker","push",remote])
    return ok, remote


# ─── docker-compose ───────────────────────────────────────────────────────────

def generate_compose(path: Path, image: str, svc: str, port: int, env: dict) -> Path:
    env_block = ""
    if env:
        lines = "\n".join(f"      - {k}={v}" for k,v in env.items())
        env_block = f"    environment:\n{lines}\n"

    body = (
        f"# Auto-generated by ai:deploy\n"
        f"version: \"3.9\"\n\n"
        f"services:\n"
        f"  {svc}:\n"
        f"    image: {image}\n"
        f"    container_name: {svc}-container\n"
        f"    restart: unless-stopped\n"
        f"    ports:\n"
        f"      - \"{port}:{port}\"\n"
        f"{env_block}"
        f"    healthcheck:\n"
        f"      test: [\"CMD-SHELL\", \"wget -qO- http://localhost:{port}/ 2>/dev/null || exit 0\"]\n"
        f"      interval: 30s\n"
        f"      timeout: 10s\n"
        f"      retries: 3\n"
        f"      start_period: 15s\n"
        f"    logging:\n"
        f"      driver: json-file\n"
        f"      options:\n"
        f"        max-size: \"10m\"\n"
        f"        max-file: \"3\"\n\n"
        f"networks:\n"
        f"  default:\n"
        f"    name: {svc}-network\n"
    )
    f = path/"docker-compose.yml"
    f.write_text(body)
    return f

def compose_up(path: Path)   -> bool:
    return _run(_compose_exe()+["up","-d","--remove-orphans"], cwd=path)

def compose_down(path: Path) -> bool:
    return _run(_compose_exe()+["down","--volumes","--remove-orphans"], cwd=path)


# ─── kubernetes manifests ─────────────────────────────────────────────────────

def generate_k8s_manifests(path: Path, image: str, name: str,
                            port: int, env: dict, replicas: int = 2) -> Path:
    env_block = ""
    if env:
        lines = "\n".join(
            f"          - name: {k}\n            value: \"{v}\"" for k,v in env.items()
        )
        env_block = f"        env:\n{lines}\n"

    body = f"""\
# Auto-generated by ai:deploy  |  app: {name}
---
apiVersion: v1
kind: Namespace
metadata:
  name: {name}
  labels:
    managed-by: ai-deploy
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {name}
  namespace: {name}
  labels:
    app: {name}
    managed-by: ai-deploy
spec:
  replicas: {replicas}
  selector:
    matchLabels:
      app: {name}
  template:
    metadata:
      labels:
        app: {name}
    spec:
      containers:
        - name: {name}
          image: {image}
          imagePullPolicy: Always
          ports:
            - containerPort: {port}
{env_block}          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
            limits:
              cpu: "500m"
              memory: "512Mi"
          livenessProbe:
            httpGet:
              path: /
              port: {port}
            initialDelaySeconds: 15
            periodSeconds: 20
          readinessProbe:
            httpGet:
              path: /
              port: {port}
            initialDelaySeconds: 5
            periodSeconds: 10
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
---
apiVersion: v1
kind: Service
metadata:
  name: {name}-service
  namespace: {name}
  labels:
    app: {name}
    managed-by: ai-deploy
spec:
  selector:
    app: {name}
  ports:
    - protocol: TCP
      port: 80
      targetPort: {port}
  type: LoadBalancer
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {name}-hpa
  namespace: {name}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {name}
  minReplicas: {replicas}
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
"""
    d = path/"k8s"
    d.mkdir(exist_ok=True)
    f = d/"deployment.yaml"
    f.write_text(body)
    return f

def k8s_apply(f: Path)     -> bool: return _run(["kubectl","apply","-f",str(f)])
def k8s_wait(name: str)    -> bool:
    return _run(["kubectl","rollout","status",f"deployment/{name}",f"-n={name}","--timeout=120s"])
def k8s_delete(name: str)  -> bool:
    return _run(["kubectl","delete","namespace",name,"--ignore-not-found=true"])

def k8s_url(name: str) -> str:
    for field in (".status.loadBalancer.ingress[0].ip",
                  ".status.loadBalancer.ingress[0].hostname"):
        r = subprocess.run(
            ["kubectl","get","svc",f"{name}-service",f"-n={name}",f"-o=jsonpath={{{field}}}"],
            capture_output=True, text=True)
        if r.stdout.strip(): return r.stdout.strip()
    return f"<pending — kubectl get svc -n {name}>"


# ─── PUBLIC API ───────────────────────────────────────────────────────────────

def run_deploy_docker(
    project_path: str | Path = ".",
    image_name:   str | None  = None,
    registry:     str | None  = None,
    overwrite_dockerfile: bool = True,
) -> int:
    path = Path(project_path).resolve()
    if not image_name: image_name = _safe_name(path.name)
    total = 6 + (1 if registry else 0)

    _banner("  ai:deploy docker  —  One-Click Container Deployment  ")
    if not path.is_dir():   _fail(f"Directory not found: {path}"); return 1
    if not _docker_ok():    _fail("Docker is not running — start Docker Desktop first"); return 1

    _step(1,total,"Detecting language / framework …")
    fw, profile = detect_framework(path)
    entry = _find_entry(path, profile)
    _ok(f"Language: {_c('bold',fw)}   Port: {profile['port']}   Entry: {entry}")

    _step(2,total,"Generating Dockerfile …")
    df = path/"Dockerfile"
    if df.exists() and not overwrite_dockerfile:
        _warn("Keeping existing Dockerfile  (pass overwrite_dockerfile=True to regenerate)")
    else:
        generate_dockerfile(path, fw, profile)
        _ok(f"Wrote {df}")

    local_tag = f"{image_name}:latest"
    _step(3,total,f"Building image  {_c('bold',local_tag)} …")
    if not build_image(path, local_tag): _fail("docker build failed"); return 1
    _ok(f"Image ready: {local_tag}")

    img4compose = local_tag
    if registry:
        _step(4,total,f"Pushing to {_c('bold',registry)} …")
        ok, remote = push_image(local_tag, registry)
        if ok:  img4compose = remote; _ok(f"Pushed: {remote}")
        else:   _warn("Push failed — using local image")

    n = 5 if registry else 4
    _step(n,total,"Writing docker-compose.yml …")
    cfile = generate_compose(path, img4compose, image_name, profile["port"], _dotenv(path))
    _ok(f"Wrote {cfile}")

    n = 6 if registry else 5
    _step(n,total,"Starting containers …")
    if not compose_up(path): _fail("docker compose up failed"); return 1
    _ok("Containers running!")

    n = 7 if registry else 6
    _step(n,total,"Done!")
    url = f"http://localhost:{profile['port']}"
    print(f"""
  {_c('bold','┌──────────────────────────────────────────────────────────────┐')}
  │                                                              │
  │   {_c('green',_c('bold','DOCKER DEPLOYMENT SUCCESSFUL'))}                          │
  │                                                              │
  │   Language  :  {fw:<46}│
  │   Image     :  {local_tag:<46}│
  │   Access    :  {_c('cyan',url):<55}│
  │                                                              │
  │   {_c('dim','docker compose logs -f')}                                     │
  │   {_c('dim','docker compose ps')}                                          │
  │   {_c('dim','ai:destroy')}          ← one-click teardown                  │
  │                                                              │
  {_c('bold','└──────────────────────────────────────────────────────────────┘')}
""")
    return 0


def run_deploy_k8s(
    project_path: str | Path = ".",
    image_name:   str | None  = None,
    registry:     str | None  = None,
    replicas:     int         = 2,
    overwrite_dockerfile: bool = True,
) -> int:
    path = Path(project_path).resolve()
    if not image_name: image_name = _safe_name(path.name)

    _banner("  ai:deploy kubernetes  —  One-Click K8s Deployment  ")
    if not path.is_dir():  _fail(f"Directory not found: {path}"); return 1
    if not _docker_ok():   _fail("Docker is not running"); return 1
    if not _kubectl_ok():  _fail("kubectl not found — install kubectl and configure a cluster"); return 1

    _step(1,7,"Detecting language / framework …")
    fw, profile = detect_framework(path)
    entry = _find_entry(path, profile)
    _ok(f"Language: {_c('bold',fw)}   Port: {profile['port']}   Entry: {entry}")

    _step(2,7,"Generating Dockerfile …")
    df = path/"Dockerfile"
    if df.exists() and not overwrite_dockerfile:
        _warn("Keeping existing Dockerfile")
    else:
        generate_dockerfile(path, fw, profile)
        _ok(f"Wrote {df}")

    local_tag = f"{image_name}:latest"
    _step(3,7,f"Building image  {_c('bold',local_tag)} …")
    if not build_image(path, local_tag): _fail("docker build failed"); return 1
    _ok(f"Image ready: {local_tag}")

    img4k8s = local_tag
    if not registry:
        _warn("No --registry — K8s nodes may not pull a local-only image")
        _warn("Works fine with minikube / kind; for cloud clusters use --registry")
    else:
        _step(4,7,f"Pushing to {_c('bold',registry)} …")
        ok, remote = push_image(local_tag, registry)
        if ok:  img4k8s = remote; _ok(f"Pushed: {remote}")
        else:   _warn("Push failed — continuing with local image")

    _step(5,7,"Generating k8s/deployment.yaml …")
    mf = generate_k8s_manifests(path, img4k8s, image_name, profile["port"], _dotenv(path), replicas)
    _ok(f"Wrote {mf}")

    _step(6,7,"Applying manifests …")
    if not k8s_apply(mf): _fail("kubectl apply failed"); return 1
    _ok("Manifests applied")

    _step(7,7,"Waiting for rollout …")
    k8s_wait(image_name)
    svc = k8s_url(image_name)
    _ok("Rollout complete")

    print(f"""
  {_c('bold','┌──────────────────────────────────────────────────────────────┐')}
  │                                                              │
  │   {_c('green',_c('bold','KUBERNETES DEPLOYMENT SUCCESSFUL'))}                     │
  │                                                              │
  │   Language   :  {fw:<45}│
  │   Image      :  {img4k8s:<45}│
  │   Namespace  :  {image_name:<45}│
  │   Replicas   :  {str(replicas):<45}│
  │   Service    :  {svc:<45}│
  │                                                              │
  │   {_c('dim',f'kubectl get pods -n {image_name}')}
  │   {_c('dim',f'kubectl logs -n {image_name} -l app={image_name} -f')}
  │   {_c('dim','ai:destroy --target kubernetes')}   ← one-click teardown     │
  │                                                              │
  {_c('bold','└──────────────────────────────────────────────────────────────┘')}
""")
    return 0


def run_destroy(
    project_path: str | Path = ".",
    image_name:   str | None  = None,
    target:       str         = "docker",
) -> int:
    path = Path(project_path).resolve()
    if not image_name: image_name = _safe_name(path.name)

    _banner("  ai:destroy  —  One-Click Teardown  ")

    if target in ("docker","all"):
        _step(1,3,"Stopping Docker Compose services …")
        if (path/"docker-compose.yml").exists():
            ok = compose_down(path)
            _ok("Compose stopped") if ok else _warn("compose down had errors (continuing)")
        else:
            _warn("No docker-compose.yml found")

        _step(2,3,f"Removing image  {image_name}:latest …")
        r = subprocess.run(["docker","rmi","-f",f"{image_name}:latest"],capture_output=True)
        _ok("Image removed") if r.returncode==0 else _warn("Image not found or already removed")

    if target in ("kubernetes","all"):
        _step(3 if target=="all" else 1, 3 if target=="all" else 2,
              f"Deleting K8s namespace  {image_name} …")
        ok = k8s_delete(image_name)
        _ok(f"Namespace '{image_name}' deleted") if ok else _warn("kubectl delete had errors")

        if target != "all":
            _step(2,2,f"Removing image  {image_name}:latest …")
            r = subprocess.run(["docker","rmi","-f",f"{image_name}:latest"],capture_output=True)
            _ok("Image removed") if r.returncode==0 else _warn("Image already gone")

    print(f"\n  {_c('green',_c('bold','✔  All done — environment is clean.'))}  🎉\n")
    return 0
