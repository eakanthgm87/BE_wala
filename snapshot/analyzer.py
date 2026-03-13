import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from .models import ProjectSnapshot, SnapshotComparison
from .snapshot_manager import SnapshotManager

class SnapshotAnalyzer:
    """AI-powered analysis of snapshots and changes."""

    def __init__(self, manager: SnapshotManager):
        self.manager = manager

    def analyze_snapshot(self, snapshot_name: str) -> str:
        """Analyze a single snapshot for insights."""
        snapshot = self.manager.storage.load_snapshot(snapshot_name)
        if not snapshot:
            return f"Snapshot '{snapshot_name}' not found."

        analysis = []
        analysis.append(f"📊 Analysis of snapshot '{snapshot_name}'")
        analysis.append(f"Created: {snapshot.timestamp}")
        analysis.append(f"Type: {snapshot.snapshot_type}")
        analysis.append("")

        # File analysis
        analysis.append(f"📁 Files: {snapshot.total_files} ({snapshot.total_size_mb:.1f} MB)")
        if snapshot.files:
            # Count by extension
            extensions = {}
            for f in snapshot.files:
                ext = os.path.splitext(f.path)[1] or 'no-ext'
                extensions[ext] = extensions.get(ext, 0) + 1

            top_ext = sorted(extensions.items(), key=lambda x: x[1], reverse=True)[:5]
            analysis.append(f"Top file types: {', '.join(f'{ext}: {count}' for ext, count in top_ext)}")

        # Process analysis
        if snapshot.processes:
            analysis.append(f"⚙️ Running processes: {len(snapshot.processes)}")
            high_cpu = [p for p in snapshot.processes if p.cpu_percent > 50]
            if high_cpu:
                analysis.append(f"High CPU processes: {', '.join(p.name for p in high_cpu[:3])}")

        # System analysis
        analysis.append(f"💻 System: CPU {snapshot.system.cpu_usage:.1f}%, "
                       f"Memory {snapshot.system.memory_used/1024/1024/1024:.1f}GB used")

        # Git analysis
        if snapshot.git.branch:
            analysis.append(f"🔀 Git: Branch '{snapshot.git.branch}', "
                           f"{len(snapshot.git.uncommitted_changes)} uncommitted changes")

        # Dependency analysis
        total_deps = len(snapshot.dependencies.python_packages) + len(snapshot.dependencies.npm_packages)
        if total_deps > 0:
            analysis.append(f"📦 Dependencies: {total_deps} packages")

        return "\n".join(analysis)

    def analyze_comparison(self, comp: SnapshotComparison) -> str:
        """Analyze a snapshot comparison for insights and recommendations."""
        analysis = []
        analysis.append(f"📊 Comparison: {comp.snapshot1} → {comp.snapshot2}")
        analysis.append("")

        # File changes
        total_file_changes = len(comp.files_added) + len(comp.files_modified) + len(comp.files_deleted)
        analysis.append(f"📁 File changes: {total_file_changes}")
        if comp.files_added:
            analysis.append(f"  ➕ Added: {len(comp.files_added)} files")
        if comp.files_modified:
            analysis.append(f"  ✏️ Modified: {len(comp.files_modified)} files")
        if comp.files_deleted:
            analysis.append(f"  🗑️ Deleted: {len(comp.files_deleted)} files")

        # Dependency changes
        dep_changes = len(comp.dependencies_added) + len(comp.dependencies_removed) + len(comp.dependencies_updated)
        if dep_changes > 0:
            analysis.append(f"📦 Dependency changes: {dep_changes}")
            if comp.dependencies_added:
                analysis.append(f"  ➕ Added: {', '.join(list(comp.dependencies_added.keys())[:3])}")
            if comp.dependencies_updated:
                analysis.append(f"  ⬆️ Updated: {', '.join(list(comp.dependencies_updated.keys())[:3])}")

        # Process changes
        if comp.processes_started or comp.processes_stopped:
            analysis.append(f"⚙️ Process changes:")
            if comp.processes_started:
                analysis.append(f"  ▶️ Started: {', '.join(comp.processes_started[:3])}")
            if comp.processes_stopped:
                analysis.append(f"  ⏹️ Stopped: {', '.join(comp.processes_stopped[:3])}")

        # System changes
        if abs(comp.memory_change_mb) > 10:
            direction = "increased" if comp.memory_change_mb > 0 else "decreased"
            analysis.append(f"💾 Memory {direction} by {abs(comp.memory_change_mb):.1f} MB")

        # Risk assessment
        analysis.append(f"⚠️ Risk level: {comp.risk_level.upper()}")

        # Recommendations
        if comp.risk_level == "high":
            analysis.append("🚨 HIGH RISK - Consider testing thoroughly before deployment")
        elif comp.risk_level == "medium":
            analysis.append("⚠️ MEDIUM RISK - Review changes carefully")

        # AI-powered insights
        insights = self._generate_insights(comp)
        if insights:
            analysis.append("")
            analysis.append("🧠 AI Insights:")
            for insight in insights:
                analysis.append(f"  • {insight}")

        return "\n".join(analysis)

    def detect_anomalies(self, snapshot: ProjectSnapshot) -> List[str]:
        """Detect anomalies in a snapshot."""
        anomalies = []

        # Check for unusually large files
        large_files = [f for f in snapshot.files if f.size > 100 * 1024 * 1024]  # 100MB
        if large_files:
            anomalies.append(f"Large files detected: {', '.join(f.path for f in large_files[:3])}")

        # Check for high CPU processes
        high_cpu = [p for p in snapshot.processes if p.cpu_percent > 80]
        if high_cpu:
            anomalies.append(f"High CPU usage: {', '.join(p.name for p in high_cpu[:3])}")

        # Check for memory issues
        memory_percent = (snapshot.system.memory_used / snapshot.system.memory_total) * 100
        if memory_percent > 90:
            anomalies.append(f"High memory usage: {memory_percent:.1f}%")

        # Check for many uncommitted changes
        if len(snapshot.git.uncommitted_changes) > 50:
            anomalies.append(f"Many uncommitted changes: {len(snapshot.git.uncommitted_changes)} files")

        return anomalies

    def suggest_snapshots(self, current_operation: str) -> Optional[str]:
        """Suggest when to create snapshots based on operations."""
        suggestions = {
            "before_delete": ["rm", "del", "unlink", "remove"],
            "before_install": ["pip install", "npm install", "apt install", "brew install"],
            "before_update": ["git pull", "git merge", "upgrade", "update"],
            "before_run": ["python", "node", "npm start", "docker run"],
            "before_deploy": ["deploy", "push", "upload", "publish"]
        }

        for suggestion_type, keywords in suggestions.items():
            if any(keyword in current_operation.lower() for keyword in keywords):
                return f"🧠 AI Suggestion: Create snapshot before {suggestion_type.replace('_', ' ')}"

        return None

    def find_last_stable_snapshot(self) -> Optional[str]:
        """Find the most recent snapshot that appears stable."""
        snapshots = self.manager.list_snapshots()

        # Look for snapshots that aren't marked as having errors
        # This is a simple heuristic - in practice, you'd want more sophisticated stability detection
        for snap in snapshots:
            if snap.get('type') != 'debug':  # Avoid debug snapshots
                return snap['name']

        return None

    def _generate_insights(self, comp: SnapshotComparison) -> List[str]:
        """Generate AI insights from comparison data."""
        insights = []

        # File change patterns
        if len(comp.files_modified) > len(comp.files_added) + len(comp.files_deleted):
            insights.append("Heavy refactoring detected - many files modified")

        # Dependency changes
        if comp.dependencies_updated:
            insights.append("Dependencies updated - check for breaking changes")

        # Process changes
        if len(comp.processes_stopped) > len(comp.processes_started):
            insights.append("More processes stopped than started - possible service issues")

        # Risk-based insights
        if comp.risk_level == "high":
            insights.append("High-risk changes detected - recommend thorough testing")
            if comp.files_deleted:
                insights.append("Files deleted - ensure backups are available")

        return insights