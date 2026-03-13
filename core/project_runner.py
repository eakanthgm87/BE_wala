import os
import subprocess


# --------------------------------
# SAFE COMMAND EXECUTOR
# --------------------------------

def run_command(command):

    try:

        print(f"$ {command}\n")

        result = subprocess.run(
            command,
            shell=True,
            text=True,
            capture_output=True
        )

        if result.stdout:
            print(result.stdout)

        if result.returncode != 0:

            print("❌ Command failed")

            if result.stderr:
                print(result.stderr)

            return False

        return True

    except Exception as e:

        print("❌ Failed to run command")
        print(e)

        return False


# --------------------------------
# DETECT PROJECT TYPE
# --------------------------------

def detect_project():

    if os.path.exists("pom.xml"):
        return "spring-maven"

    if os.path.exists("build.gradle"):
        return "spring-gradle"

    if os.path.exists("package.json"):
        return "node"

    if os.path.exists("requirements.txt") or any(f.endswith(".py") for f in os.listdir()):
        return "python"

    if os.path.exists("go.mod"):
        return "go"

    if os.path.exists("Cargo.toml"):
        return "rust"

    if os.path.exists("docker-compose.yml") or os.path.exists("Dockerfile"):
        return "docker"

    return "unknown"


# --------------------------------
# SCAN PROJECT
# --------------------------------

def scan_project(project):

    print("🔎 Step 1: Scanning project...\n")

    if project == "python":

        print("Checking Python syntax...\n")

        for file in os.listdir():

            if file.endswith(".py"):

                ok = run_command(f"python -m py_compile {file}")

                if not ok:
                    return False

    elif project == "node":

        return run_command("npm install --dry-run")

    elif project == "spring-maven":

        return run_command("mvn -q validate")

    elif project == "spring-gradle":

        return run_command("gradle tasks")

    elif project == "go":

        return run_command("go build ./...")

    elif project == "rust":

        return run_command("cargo check")

    elif project == "docker":

        print("Checking Docker configuration")

        if not os.path.exists("Dockerfile"):
            print("⚠ Dockerfile missing")

    else:

        print("⚠ Unknown project type")

    return True


# --------------------------------
# INSTALL DEPENDENCIES
# --------------------------------

def install_dependencies(project):

    print("\n📦 Step 2: Installing dependencies\n")

    if project == "python":

        if os.path.exists("requirements.txt"):
            return run_command("pip install -r requirements.txt")

    elif project == "node":

        return run_command("npm install")

    elif project == "spring-maven":

        return run_command("mvn clean install")

    elif project == "spring-gradle":

        return run_command("gradle build")

    elif project == "go":

        return run_command("go mod tidy")

    elif project == "rust":

        return run_command("cargo build")

    elif project == "docker":

        print("Docker dependencies handled during build")

    return True


# --------------------------------
# BUILD PROJECT
# --------------------------------

def build_project(project):

    print("\n🏗 Step 3: Building project\n")

    if project == "node":

        return run_command("npm run build")

    elif project == "spring-maven":

        return run_command("mvn clean package")

    elif project == "spring-gradle":

        return run_command("gradle build")

    elif project == "go":

        return run_command("go build")

    elif project == "rust":

        return run_command("cargo build")

    elif project == "docker":

        return run_command("docker build -t shellmind-app .")

    else:

        print("ℹ Build step not required")

    return True


# --------------------------------
# RUN PROJECT
# --------------------------------

def run_project_app(project):

    print("\n🚀 Step 4: Running project\n")

    if project == "python":

        for entry in ["main.py", "app.py", "run.py", "server.py"]:

            if os.path.exists(entry):
                return run_command(f"python {entry}")

        print("⚠ No Python entry file found")

    elif project == "node":

        return run_command("npm start")

    elif project == "spring-maven":

        return run_command("mvn spring-boot:run")

    elif project == "spring-gradle":

        return run_command("gradle bootRun")

    elif project == "go":

        return run_command("go run main.go")

    elif project == "rust":

        return run_command("cargo run")

    elif project == "docker":

        return run_command("docker compose up")

    else:

        print("❌ Could not determine how to run this project")

    return True


# --------------------------------
# FULL PIPELINE
# --------------------------------

def run_project():

    print("\n================================")
    print("       ShellMind Project Run")
    print("================================\n")

    project = detect_project()

    print(f"Detected project type: {project}\n")

    if not scan_project(project):
        print("❌ Project scan failed")
        return

    if not install_dependencies(project):
        print("❌ Dependency installation failed")
        return

    if not build_project(project):
        print("❌ Build failed")
        return

    run_project_app(project)

    print("\n✅ Project pipeline finished\n")