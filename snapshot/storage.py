import json
import os
import gzip
from pathlib import Path
from typing import List, Dict, Optional, Any
import shutil

from .models import ProjectSnapshot, SnapshotComparison

class SnapshotStorage:
    """Handles storage and retrieval of project snapshots."""

    def __init__(self, base_dir: str = None):
        if base_dir is None:
            # Default to .snapshots in current directory
            self.base_dir = Path.cwd() / ".snapshots"
        else:
            self.base_dir = Path(base_dir)

        self.base_dir.mkdir(exist_ok=True)
        self.snapshots_dir = self.base_dir / "snapshots"
        self.comparisons_dir = self.base_dir / "comparisons"
        self.metadata_file = self.base_dir / "metadata.json"

        self.snapshots_dir.mkdir(exist_ok=True)
        self.comparisons_dir.mkdir(exist_ok=True)

    def save_snapshot(self, snapshot: ProjectSnapshot) -> bool:
        """Save a snapshot to disk."""
        try:
            filename = f"{snapshot.name}_{snapshot.timestamp.strftime('%Y%m%d_%H%M%S')}.json.gz"
            filepath = self.snapshots_dir / filename

            # Convert to dict and save compressed
            data = snapshot.to_dict()
            with gzip.open(filepath, 'wt', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            # Update metadata
            self._update_metadata(snapshot.name, str(filepath))

            return True
        except Exception as e:
            print(f"Error saving snapshot: {e}")
            return False

    def load_snapshot(self, name: str) -> Optional[ProjectSnapshot]:
        """Load a snapshot by name."""
        try:
            # Find the latest snapshot with this name
            pattern = f"{name}_*.json.gz"
            files = list(self.snapshots_dir.glob(pattern))

            if not files:
                return None

            # Get the most recent
            latest_file = max(files, key=lambda f: f.stat().st_mtime)

            with gzip.open(latest_file, 'rt', encoding='utf-8') as f:
                data = json.load(f)

            return ProjectSnapshot.from_dict(data)

        except Exception as e:
            print(f"Error loading snapshot '{name}': {e}")
            return None

    def list_snapshots(self) -> List[Dict[str, str]]:
        """List all available snapshots."""
        snapshots = []

        try:
            for file in self.snapshots_dir.glob("*.json.gz"):
                try:
                    with gzip.open(file, 'rt', encoding='utf-8') as f:
                        data = json.load(f)

                    snapshots.append({
                        'name': data['name'],
                        'timestamp': data['timestamp'],
                        'type': data.get('snapshot_type', 'manual'),
                        'description': data.get('description', ''),
                        'file': str(file)
                    })

                except Exception:
                    continue

        except Exception:
            pass

        # Sort by timestamp descending
        snapshots.sort(key=lambda x: x['timestamp'], reverse=True)
        return snapshots

    def delete_snapshot(self, name: str) -> bool:
        """Delete a snapshot by name."""
        try:
            pattern = f"{name}_*.json.gz"
            files = list(self.snapshots_dir.glob(pattern))

            if not files:
                return False

            # Delete all versions
            for file in files:
                file.unlink()

            # Update metadata
            self._update_metadata(name, None)

            return True
        except Exception as e:
            print(f"Error deleting snapshot '{name}': {e}")
            return False

    def save_comparison(self, comparison: SnapshotComparison) -> bool:
        """Save a snapshot comparison."""
        try:
            filename = f"comparison_{comparison.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.comparisons_dir / filename

            data = {
                'snapshot1': comparison.snapshot1,
                'snapshot2': comparison.snapshot2,
                'timestamp': comparison.timestamp.isoformat(),
                'files_added': comparison.files_added,
                'files_modified': comparison.files_modified,
                'files_deleted': comparison.files_deleted,
                'dependencies_added': comparison.dependencies_added,
                'dependencies_removed': comparison.dependencies_removed,
                'dependencies_updated': comparison.dependencies_updated,
                'processes_started': comparison.processes_started,
                'processes_stopped': comparison.processes_stopped,
                'memory_change_mb': comparison.memory_change_mb,
                'disk_change_mb': comparison.disk_change_mb,
                'risk_level': comparison.risk_level,
                'recommendations': comparison.recommendations
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            return True
        except Exception as e:
            print(f"Error saving comparison: {e}")
            return False

    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        try:
            total_size = 0
            snapshot_count = 0

            for file in self.snapshots_dir.glob("*.json.gz"):
                total_size += file.stat().st_size
                snapshot_count += 1

            return {
                'total_snapshots': snapshot_count,
                'total_size_mb': total_size / (1024 * 1024),
                'storage_path': str(self.base_dir)
            }
        except Exception:
            return {'error': 'Could not read storage stats'}

    def _update_metadata(self, name: str, filepath: Optional[str]):
        """Update the metadata file."""
        try:
            metadata = {}

            if self.metadata_file.exists():
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

            if filepath:
                metadata[name] = filepath
            elif name in metadata:
                del metadata[name]

            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)

        except Exception:
            pass  # Metadata is optional