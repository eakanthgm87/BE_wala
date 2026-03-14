import os
import psutil
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime

from .models import (
    ProjectSnapshot, FileSnapshot, ProcessSnapshot,
    SystemSnapshot, GitSnapshot, DependencySnapshot,
    EnvironmentSnapshot, SnapshotComparison
)
from .storage import SnapshotStorage

class SnapshotManager:
    """Main class for managing project snapshots."""

    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.storage = SnapshotStorage(str(self.project_root / ".snapshots"))

        # File size limits
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.max_files = 1000

    def create_snapshot(self, name: str, description: str = "",
                       snapshot_type: str = "manual") -> ProjectSnapshot:
        """Create a new project snapshot."""
        print(f"📸 Creating snapshot: {name}")

        snapshot = ProjectSnapshot(
            name=name,
            description=description,
            snapshot_type=snapshot_type,
            project_root=str(self.project_root)
        )

        # Capture different aspects
        snapshot.files = self._capture_files()
        snapshot.processes = self._capture_processes()
        snapshot.system = self._capture_system()
        snapshot.git = self._capture_git()
        snapshot.dependencies = self._capture_dependencies()
        snapshot.environment = self._capture_environment()

        # Calculate totals
        snapshot.total_files = len(snapshot.files)
        snapshot.total_size_mb = sum(f.size for f in snapshot.files) / (1024 * 1024)

        # Save to storage
        if self.storage.save_snapshot(snapshot):
            print(f"✔ Snapshot '{name}' created successfully")
            print(f"  📁 {snapshot.total_files} files")
            print(f"  💾 {snapshot.total_size_mb:.1f} MB")
        else:
            print(f"❌ Failed to save snapshot '{name}'")

        return snapshot

    def restore_snapshot(self, name: str) -> bool:
        """Restore a project to a previous snapshot."""
        print(f"⏪ Restoring snapshot: {name}")

        snapshot = self.storage.load_snapshot(name)
        if not snapshot:
            print(f"❌ Snapshot '{name}' not found")
            return False

        try:
            # Restore files
            self._restore_files(snapshot)

            # Note: Other aspects (processes, system) cannot be fully restored
            # but we can attempt to restart services, etc.

            print(f"✔ Snapshot '{name}' restored successfully")
            return True

        except Exception as e:
            print(f"❌ Error restoring snapshot: {e}")
            return False

    def compare_snapshots(self, name1: str, name2: str) -> Optional[SnapshotComparison]:
        """Compare two snapshots."""
        snap1 = self.storage.load_snapshot(name1)
        snap2 = self.storage.load_snapshot(name2)

        if not snap1 or not snap2:
            print("❌ One or both snapshots not found")
            return None

        comparison = SnapshotComparison(
            snapshot1=name1,
            snapshot2=name2
        )

        # Compare files
        self._compare_files(snap1, snap2, comparison)

        # Compare dependencies
        self._compare_dependencies(snap1, snap2, comparison)

        # Compare processes
        self._compare_processes(snap1, snap2, comparison)

        # Calculate system changes
        comparison.memory_change_mb = snap2.system.memory_used - snap1.system.memory_used

        # Assess risk level
        comparison.risk_level = self._assess_risk(comparison)

        # Save comparison
        self.storage.save_comparison(comparison)

        return comparison

    def list_snapshots(self) -> List[Dict[str, str]]:
        """List all available snapshots."""
        return self.storage.list_snapshots()

    def delete_snapshot(self, name: str) -> bool:
        """Delete a snapshot."""
        return self.storage.delete_snapshot(name)

    def auto_snapshot(self, operation: str) -> Optional[str]:
        """Create automatic snapshot before risky operations."""
        risky_ops = {
            'delete': ['rm', 'del', 'remove'],
            'install': ['pip install', 'npm install', 'apt install'],
            'update': ['git pull', 'git merge', 'update'],
            'run': ['python', 'node', 'npm start']
        }

        for category, commands in risky_ops.items():
            if any(cmd in operation.lower() for cmd in commands):
                name = f"auto-{category}-{datetime.now().strftime('%H%M%S')}"
                self.create_snapshot(name, f"Auto-snapshot before: {operation}",
                                   snapshot_type="auto")
                return name

        return None

    def _capture_files(self) -> List[FileSnapshot]:
        """Capture all project files."""
        files = []
        count = 0

        for root, dirs, files_in_dir in os.walk(self.project_root):
            # Skip snapshot directory and common ignores
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']

            for file in files_in_dir:
                if count >= self.max_files:
                    break

                filepath = Path(root) / file
                rel_path = filepath.relative_to(self.project_root)

                try:
                    stat = filepath.stat()
                    size = stat.st_size

                    if size > self.max_file_size:
                        continue

                    # Check if binary
                    is_binary = self._is_binary_file(filepath)

                    content = None
                    if not is_binary:
                        try:
                            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                        except:
                            is_binary = True

                    files.append(FileSnapshot(
                        path=str(rel_path),
                        content=content,
                        size=size,
                        mtime=stat.st_mtime,
                        is_binary=is_binary
                    ))

                    count += 1

                except Exception:
                    continue

        return files

    def _capture_processes(self) -> List[ProcessSnapshot]:
        """Capture running processes."""
        processes = []

        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_info']):
                try:
                    info = proc.info
                    if info['cmdline']:
                        processes.append(ProcessSnapshot(
                            pid=info['pid'],
                            name=info['name'] or '',
                            cmdline=info['cmdline'],
                            cpu_percent=info['cpu_percent'] or 0.0,
                            memory_mb=(info['memory_info'].rss / (1024 * 1024)) if info['memory_info'] else 0.0
                        ))
                except:
                    continue
        except:
            pass

        return processes[:50]  # Limit to 50 processes

    def _capture_system(self) -> SystemSnapshot:
        """Capture system information."""
        system = SystemSnapshot()

        try:
            system.cpu_usage = psutil.cpu_percent(interval=1)

            mem = psutil.virtual_memory()
            system.memory_total = mem.total
            system.memory_used = mem.used

            # Disk usage
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    system.disk_usage[partition.mountpoint] = {
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': usage.percent
                    }
                except:
                    continue

            # Network connections (limit to 20)
            connections = psutil.net_connections()
            for conn in connections[:20]:
                system.network_connections.append({
                    'fd': conn.fd,
                    'family': str(conn.family),
                    'type': str(conn.type),
                    'laddr': str(conn.laddr) if conn.laddr else None,
                    'raddr': str(conn.raddr) if conn.raddr else None,
                    'status': conn.status
                })

        except Exception:
            pass

        return system

    def _capture_git(self) -> GitSnapshot:
        """Capture git repository state."""
        git = GitSnapshot()

        try:
            # Get current branch
            result = subprocess.run(['git', 'branch', '--show-current'],
                                  cwd=self.project_root, capture_output=True, text=True)
            if result.returncode == 0:
                git.branch = result.stdout.strip()

            # Get status
            result = subprocess.run(['git', 'status', '--porcelain'],
                                  cwd=self.project_root, capture_output=True, text=True)
            if result.returncode == 0:
                git.status = result.stdout

            # Get last commit
            result = subprocess.run(['git', 'log', '-1', '--oneline'],
                                  cwd=self.project_root, capture_output=True, text=True)
            if result.returncode == 0:
                git.last_commit = result.stdout.strip()

            # Get uncommitted changes
            result = subprocess.run(['git', 'diff', '--name-only'],
                                  cwd=self.project_root, capture_output=True, text=True)
            if result.returncode == 0:
                git.uncommitted_changes = result.stdout.strip().split('\n') if result.stdout.strip() else []

            # Get staged files
            result = subprocess.run(['git', 'diff', '--cached', '--name-only'],
                                  cwd=self.project_root, capture_output=True, text=True)
            if result.returncode == 0:
                git.staged_files = result.stdout.strip().split('\n') if result.stdout.strip() else []

        except Exception:
            pass

        return git

    def _capture_dependencies(self) -> DependencySnapshot:
        """Capture project dependencies."""
        deps = DependencySnapshot()

        # Python packages
        try:
            result = subprocess.run(['pip', 'list', '--format=json'],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                import json
                packages = json.loads(result.stdout)
                deps.python_packages = {pkg['name']: pkg['version'] for pkg in packages}
        except:
            pass

        # Node packages
        package_json = self.project_root / 'package.json'
        if package_json.exists():
            try:
                import json
                with open(package_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    deps.npm_packages = data.get('dependencies', {})
            except:
                pass

        return deps

    def _capture_environment(self) -> EnvironmentSnapshot:
        """Capture environment information."""
        env = EnvironmentSnapshot()

        # Environment variables (filter sensitive ones)
        sensitive_keys = {'password', 'secret', 'key', 'token', 'auth'}
        for key, value in os.environ.items():
            if not any(s in key.lower() for s in sensitive_keys):
                env.env_vars[key] = value

        # Python version
        try:
            import sys
            env.python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        except:
            pass

        # Node version
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                env.node_version = result.stdout.strip()
        except:
            pass

        env.working_directory = str(self.project_root)

        return env

    def _restore_files(self, snapshot: ProjectSnapshot):
        """Restore files from snapshot."""
        for file_snapshot in snapshot.files:
            filepath = self.project_root / file_snapshot.path

            # Create directory if needed
            filepath.parent.mkdir(parents=True, exist_ok=True)

            # Restore file content
            if file_snapshot.content is not None:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(file_snapshot.content)
            elif not file_snapshot.is_binary:
                # Create empty file
                filepath.touch()

    def _compare_files(self, snap1: ProjectSnapshot, snap2: ProjectSnapshot,
                      comparison: SnapshotComparison):
        """Compare files between snapshots."""
        files1 = {f.path: f for f in snap1.files}
        files2 = {f.path: f for f in snap2.files}

        # Files added
        comparison.files_added = [path for path in files2.keys() if path not in files1]

        # Files deleted
        comparison.files_deleted = [path for path in files1.keys() if path not in files2]

        # Files modified
        for path in files1.keys() & files2.keys():
            f1, f2 = files1[path], files2[path]
            if f1.mtime != f2.mtime or f1.size != f2.size:
                comparison.files_modified.append(path)

    def _compare_dependencies(self, snap1: ProjectSnapshot, snap2: ProjectSnapshot,
                            comparison: SnapshotComparison):
        """Compare dependencies between snapshots."""
        deps1, deps2 = snap1.dependencies, snap2.dependencies

        # Python packages
        for name, version in deps2.python_packages.items():
            if name not in deps1.python_packages:
                comparison.dependencies_added[name] = version
            elif deps1.python_packages[name] != version:
                comparison.dependencies_updated[name] = (deps1.python_packages[name], version)

        for name in deps1.python_packages.keys():
            if name not in deps2.python_packages:
                comparison.dependencies_removed[name] = deps1.python_packages[name]

    def _compare_processes(self, snap1: ProjectSnapshot, snap2: ProjectSnapshot,
                          comparison: SnapshotComparison):
        """Compare processes between snapshots."""
        procs1 = {p.pid: p for p in snap1.processes}
        procs2 = {p.pid: p for p in snap2.processes}

        # Processes started
        comparison.processes_started = [p.name for p in procs2.values() if p.pid not in procs1]

        # Processes stopped
        comparison.processes_stopped = [p.name for p in procs1.values() if p.pid not in procs2]

    def _assess_risk(self, comparison: SnapshotComparison) -> str:
        """Assess risk level of changes."""
        risk_score = 0

        risk_score += len(comparison.files_deleted) * 2
        risk_score += len(comparison.dependencies_removed) * 3
        risk_score += len(comparison.processes_stopped) * 1

        if risk_score > 10:
            return "high"
        elif risk_score > 5:
            return "medium"
        else:
            return "low"

    def _is_binary_file(self, filepath: Path) -> bool:
        """Check if file is binary."""
        try:
            with open(filepath, 'rb') as f:
                chunk = f.read(1024)
                if b'\0' in chunk:
                    return True
                # Try to decode as text
                chunk.decode('utf-8')
                return False
        except:
            return True