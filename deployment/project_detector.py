import os
import json
import yaml
from pathlib import Path

class ProjectAnalyzer:
    """
    AI-powered project analysis
    Detects frameworks, dependencies, and architecture
    """

    def analyze(self, path):
        return {
            'frameworks': self.detect_frameworks(path),
            'dependencies': self.scan_dependencies(path),
            'services': self.detect_services(path),
            'databases': self.detect_databases(path),
            'env_vars': self.extract_env_vars(path),
            'ports': self.detect_ports(path),
            'build_commands': self.detect_build_commands(path),
            'entry_points': self.find_entry_points(path),
            'architecture': self.determine_architecture(path)
        }

    def detect_frameworks(self, path):
        """Detect all frameworks in project"""
        frameworks = []

        # Check package files
        if os.path.exists(f"{path}/package.json"):
            try:
                pkg = json.load(open(f"{path}/package.json"))
                deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}

                if 'react' in deps: frameworks.append('react')
                if 'vue' in deps: frameworks.append('vue')
                if 'express' in deps: frameworks.append('express')
                if 'next' in deps: frameworks.append('nextjs')
            except:
                pass

        if os.path.exists(f"{path}/requirements.txt"):
            try:
                reqs = open(f"{path}/requirements.txt").read().lower()
                if 'fastapi' in reqs: frameworks.append('fastapi')
                if 'django' in reqs: frameworks.append('django')
                if 'flask' in reqs: frameworks.append('flask')
            except:
                pass

        # If no frameworks detected but there are Python files, assume generic Python
        if not frameworks:
            python_files = list(Path(path).glob("*.py"))
            if python_files:
                frameworks.append('python')

        return frameworks

        return frameworks

    def scan_dependencies(self, path):
        """Scan project dependencies"""
        dependencies = []

        # Check requirements.txt
        if os.path.exists(f"{path}/requirements.txt"):
            try:
                with open(f"{path}/requirements.txt") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            dep = line.split('==')[0].split('>=')[0].split('<')[0].strip()
                            dependencies.append(dep)
            except:
                pass

        # Check package.json
        if os.path.exists(f"{path}/package.json"):
            try:
                import json
                pkg = json.load(open(f"{path}/package.json"))
                deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}
                dependencies.extend(list(deps.keys()))
            except:
                pass

        return dependencies

    def detect_services(self, path):
        """Detect microservices structure"""
        services = []

        # Look for service indicators
        if os.path.exists(f"{path}/docker-compose.yml"):
            try:
                compose = yaml.safe_load(open(f"{path}/docker-compose.yml"))
                services = list(compose.get('services', {}).keys())
            except:
                pass

        # Look for service folders
        for item in os.listdir(path):
            if os.path.isdir(f"{path}/{item}"):
                if os.path.exists(f"{path}/{item}/Dockerfile"):
                    services.append(item)
                elif os.path.exists(f"{path}/{item}/package.json"):
                    services.append(item)

        return services

    def detect_databases(self, path):
        """Detect database usage"""
        databases = []

        # Check requirements for database drivers
        if os.path.exists(f"{path}/requirements.txt"):
            try:
                reqs = open(f"{path}/requirements.txt").read().lower()
                if 'psycopg2' in reqs or 'sqlalchemy' in reqs: databases.append('postgresql')
                if 'pymongo' in reqs: databases.append('mongodb')
                if 'redis' in reqs: databases.append('redis')
            except:
                pass

        # Check for database config files
        if os.path.exists(f"{path}/docker-compose.yml"):
            try:
                compose = yaml.safe_load(open(f"{path}/docker-compose.yml"))
                for service in compose.get('services', {}).values():
                    image = service.get('image', '').lower()
                    if 'postgres' in image: databases.append('postgresql')
                    if 'mongo' in image: databases.append('mongodb')
                    if 'redis' in image: databases.append('redis')
            except:
                pass

        return databases

    def extract_env_vars(self, path):
        """Extract environment variables from files"""
        env_vars = {}

        # Check .env files
        for env_file in ['.env', '.env.local', '.env.production']:
            if os.path.exists(f"{path}/{env_file}"):
                try:
                    with open(f"{path}/{env_file}") as f:
                        for line in f:
                            if '=' in line and not line.startswith('#'):
                                key, value = line.strip().split('=', 1)
                                env_vars[key] = value
                except:
                    pass

        return env_vars

    def detect_ports(self, path):
        """Detect ports used by the application"""
        ports = []

        # Check for port configurations
        if os.path.exists(f"{path}/docker-compose.yml"):
            try:
                compose = yaml.safe_load(open(f"{path}/docker-compose.yml"))
                for service in compose.get('services', {}).values():
                    for port_mapping in service.get('ports', []):
                        if isinstance(port_mapping, str) and ':' in port_mapping:
                            host_port = port_mapping.split(':')[0]
                            ports.append(int(host_port))
            except:
                pass

        # Default ports based on frameworks
        frameworks = self.detect_frameworks(path)
        if 'fastapi' in frameworks or 'flask' in frameworks: ports.append(8000)
        if 'django' in frameworks: ports.append(8000)
        if 'react' in frameworks: ports.append(3000)
        if 'nextjs' in frameworks: ports.append(3000)

        return list(set(ports))  # Remove duplicates

    def detect_build_commands(self, path):
        """Detect build commands"""
        commands = []

        if os.path.exists(f"{path}/package.json"):
            try:
                pkg = json.load(open(f"{path}/package.json"))
                scripts = pkg.get('scripts', {})
                if 'build' in scripts: commands.append('npm run build')
            except:
                pass

        return commands

    def find_entry_points(self, path):
        """Find application entry points"""
        entry_points = []

        # Common entry point files
        candidates = ['main.py', 'app.py', 'index.js', 'server.js', 'app.js']
        for candidate in candidates:
            if os.path.exists(f"{path}/{candidate}"):
                entry_points.append(candidate)

        return entry_points

    def determine_architecture(self, path):
        """Determine project architecture"""
        services = self.detect_services(path)

        if len(services) > 1:
            return 'microservices'
        elif os.path.exists(f"{path}/docker-compose.yml"):
            return 'containerized'
        else:
            return 'monolithic'

    # Legacy method for compatibility
    def detect_project_type(self, project_path="."):
        """Detect the framework used in the project"""
        frameworks = self.detect_frameworks(project_path)
        return frameworks[0] if frameworks else "Unknown"

    def get_project_info(self, project_path="."):
        """Get detailed project information"""
        analysis = self.analyze(project_path)

        info = {
            "framework": analysis['frameworks'][0] if analysis['frameworks'] else "Unknown",
            "path": str(Path(project_path).absolute()),
            "has_requirements": os.path.exists(f"{project_path}/requirements.txt"),
            "has_package_json": os.path.exists(f"{project_path}/package.json"),
            "has_dockerfile": os.path.exists(f"{project_path}/Dockerfile"),
            "services": analysis['services'],
            "databases": analysis['databases'],
            "ports": analysis['ports'],
            "architecture": analysis['architecture']
        }

        return info