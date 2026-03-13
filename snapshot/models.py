from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
import os

@dataclass
class FileSnapshot:
    """Represents a single file's state at a point in time."""
    path: str
    content: Optional[str] = None  # Text content (UTF-8) when available
    binary_content: Optional[str] = None  # Base64 when file is binary or non-UTF8
    size: int = 0
    mtime: float = 0.0
    is_binary: bool = False

@dataclass
class ProcessSnapshot:
    """Represents a running process."""
    pid: int
    name: str
    cmdline: List[str]
    cpu_percent: float = 0.0
    memory_mb: float = 0.0

@dataclass
class SystemSnapshot:
    """System-level information."""
    cpu_usage: float = 0.0
    memory_total: int = 0
    memory_used: int = 0
    disk_usage: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    network_connections: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class GitSnapshot:
    """Git repository state."""
    branch: str = ""
    status: str = ""
    last_commit: str = ""
    uncommitted_changes: List[str] = field(default_factory=list)
    staged_files: List[str] = field(default_factory=list)

@dataclass
class DependencySnapshot:
    """Project dependencies."""
    python_packages: Dict[str, str] = field(default_factory=dict)  # name -> version
    npm_packages: Dict[str, str] = field(default_factory=dict)
    system_packages: List[str] = field(default_factory=list)

@dataclass
class EnvironmentSnapshot:
    """Environment variables and settings."""
    env_vars: Dict[str, str] = field(default_factory=dict)
    python_version: str = ""
    node_version: str = ""
    working_directory: str = ""

@dataclass
class ProjectSnapshot:
    """Complete project state snapshot."""
    name: str
    timestamp: datetime = field(default_factory=datetime.now)
    description: str = ""

    # Core data
    files: List[FileSnapshot] = field(default_factory=list)
    processes: List[ProcessSnapshot] = field(default_factory=list)
    system: SystemSnapshot = field(default_factory=SystemSnapshot)
    git: GitSnapshot = field(default_factory=GitSnapshot)
    dependencies: DependencySnapshot = field(default_factory=DependencySnapshot)
    environment: EnvironmentSnapshot = field(default_factory=EnvironmentSnapshot)

    # Metadata
    project_root: str = ""
    total_files: int = 0
    total_size_mb: float = 0.0
    snapshot_type: str = "manual"  # manual, auto, system, debug

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'timestamp': self.timestamp.isoformat(),
            'description': self.description,
            'files': [vars(f) for f in self.files],
            'processes': [vars(p) for p in self.processes],
            'system': vars(self.system),
            'git': vars(self.git),
            'dependencies': vars(self.dependencies),
            'environment': vars(self.environment),
            'project_root': self.project_root,
            'total_files': self.total_files,
            'total_size_mb': self.total_size_mb,
            'snapshot_type': self.snapshot_type
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectSnapshot':
        """Create from dictionary."""
        # Convert timestamp
        timestamp = datetime.fromisoformat(data['timestamp'])

        # Create instance
        snapshot = cls(
            name=data['name'],
            timestamp=timestamp,
            description=data.get('description', ''),
            project_root=data.get('project_root', ''),
            total_files=data.get('total_files', 0),
            total_size_mb=data.get('total_size_mb', 0.0),
            snapshot_type=data.get('snapshot_type', 'manual')
        )

        # Restore files
        snapshot.files = [FileSnapshot(**f) for f in data.get('files', [])]

        # Restore processes
        snapshot.processes = [ProcessSnapshot(**p) for p in data.get('processes', [])]

        # Restore system
        if 'system' in data:
            snapshot.system = SystemSnapshot(**data['system'])

        # Restore git
        if 'git' in data:
            snapshot.git = GitSnapshot(**data['git'])

        # Restore dependencies
        if 'dependencies' in data:
            snapshot.dependencies = DependencySnapshot(**data['dependencies'])

        # Restore environment
        if 'environment' in data:
            snapshot.environment = EnvironmentSnapshot(**data['environment'])

        return snapshot

@dataclass
class SnapshotComparison:
    """Comparison between two snapshots."""
    snapshot1: str
    snapshot2: str
    timestamp: datetime = field(default_factory=datetime.now)

    # Changes
    files_added: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    files_deleted: List[str] = field(default_factory=list)

    dependencies_added: Dict[str, str] = field(default_factory=dict)
    dependencies_removed: Dict[str, str] = field(default_factory=dict)
    dependencies_updated: Dict[str, tuple] = field(default_factory=dict)  # name -> (old_ver, new_ver)

    processes_started: List[str] = field(default_factory=list)
    processes_stopped: List[str] = field(default_factory=list)

    memory_change_mb: float = 0.0
    disk_change_mb: float = 0.0

    # Analysis
    risk_level: str = "low"  # low, medium, high
    recommendations: List[str] = field(default_factory=list)