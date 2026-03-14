from typing import List, Dict, Any, Optional
from .snapshot_manager import SnapshotManager
from .analyzer import SnapshotAnalyzer

class SnapshotCommands:
    """Command handlers for snapshot operations."""

    def __init__(self, project_root: str = None):
        self.manager = SnapshotManager(project_root)
        self.analyzer = SnapshotAnalyzer(self.manager)

    def cmd_create(self, args: List[str]) -> str:
        """Create a new snapshot."""
        if not args:
            return "Usage: ai snapshot create <name> [description]"

        name = args[0]
        description = " ".join(args[1:]) if len(args) > 1 else ""

        snapshot = self.manager.create_snapshot(name, description)
        return f"📸 Snapshot '{name}' created successfully"

    def cmd_restore(self, args: List[str]) -> str:
        """Restore from a snapshot."""
        if not args:
            return "Usage: ai snapshot restore <name>"

        name = args[0]

        if self.manager.restore_snapshot(name):
            return f"⏪ Snapshot '{name}' restored successfully"
        else:
            return f"❌ Failed to restore snapshot '{name}'"

    def cmd_list(self, args: List[str] = None) -> str:
        """List all snapshots."""
        snapshots = self.manager.list_snapshots()

        if not snapshots:
            return "No snapshots found."

        lines = ["Snapshots:"]
        for snap in snapshots:
            desc = f" - {snap['description']}" if snap['description'] else ""
            lines.append(f"📸 {snap['name']} ({snap['type']}) - {snap['timestamp'][:19]}{desc}")

        return "\n".join(lines)

    def cmd_delete(self, args: List[str]) -> str:
        """Delete a snapshot."""
        if not args:
            return "Usage: ai snapshot delete <name>"

        name = args[0]

        if self.manager.delete_snapshot(name):
            return f"🗑️ Snapshot '{name}' deleted"
        else:
            return f"❌ Failed to delete snapshot '{name}'"

    def cmd_diff(self, args: List[str]) -> str:
        """Compare two snapshots."""
        if len(args) < 2:
            return "Usage: ai snapshot diff <snapshot1> <snapshot2>"

        name1, name2 = args[0], args[1]

        comparison = self.manager.compare_snapshots(name1, name2)
        if not comparison:
            return f"❌ Could not compare snapshots '{name1}' and '{name2}'"

        return self.analyzer.analyze_comparison(comparison)

    def cmd_analyze(self, args: List[str]) -> str:
        """Analyze a snapshot."""
        if not args:
            return "Usage: ai snapshot analyze <name>"

        name = args[0]
        return self.analyzer.analyze_snapshot(name)

    def cmd_system(self, args: List[str] = None) -> str:
        """Create a system-level snapshot."""
        name = f"system-{self._get_timestamp()}"
        snapshot = self.manager.create_snapshot(name, "System snapshot", "system")
        return f"🖥️ System snapshot '{name}' created"

    def cmd_inspect(self, args: List[str]) -> str:
        """Inspect snapshot details."""
        if not args:
            return "Usage: ai snapshot inspect <name>"

        name = args[0]
        return self.analyzer.analyze_snapshot(name)

    def cmd_recover(self, args: List[str] = None) -> str:
        """Recover to last stable snapshot."""
        stable_snapshot = self.analyzer.find_last_stable_snapshot()

        if not stable_snapshot:
            return "❌ No stable snapshots found"

        if self.manager.restore_snapshot(stable_snapshot):
            return f"🔄 Recovered to stable snapshot '{stable_snapshot}'"
        else:
            return "❌ Recovery failed"

    def cmd_undo(self, args: List[str] = None) -> str:
        """Undo last operation using most recent auto-snapshot."""
        snapshots = self.manager.list_snapshots()

        # Find most recent auto snapshot
        auto_snapshots = [s for s in snapshots if s.get('type') == 'auto']

        if not auto_snapshots:
            return "❌ No auto-snapshots found for undo"

        latest_auto = auto_snapshots[0]  # Already sorted by timestamp

        if self.manager.restore_snapshot(latest_auto['name']):
            return f"↶ Undid last operation using '{latest_auto['name']}'"
        else:
            return "❌ Undo failed"

    def cmd_timeline(self, args: List[str] = None) -> str:
        """Show timeline of snapshots."""
        snapshots = self.manager.list_snapshots()

        if not snapshots:
            return "No snapshots in timeline."

        lines = ["⏰ Snapshot Timeline:"]
        for snap in snapshots[:10]:  # Show last 10
            time_str = snap['timestamp'][:16]  # YYYY-MM-DD HH:MM
            lines.append(f"  {time_str} - {snap['name']} ({snap['type']})")

        return "\n".join(lines)

    def handle_command(self, command: str, args: List[str]) -> str:
        """Main command dispatcher."""
        subcommands = {
            'create': self.cmd_create,
            'restore': self.cmd_restore,
            'list': self.cmd_list,
            'delete': self.cmd_delete,
            'diff': self.cmd_diff,
            'analyze': self.cmd_analyze,
            'system': self.cmd_system,
            'inspect': self.cmd_inspect,
            'recover': self.cmd_recover,
            'undo': self.cmd_undo,
            'timeline': self.cmd_timeline
        }

        if command in subcommands:
            try:
                return subcommands[command](args)
            except Exception as e:
                return f"❌ Error: {str(e)}"
        else:
            return f"Unknown snapshot command: {command}"

    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        from datetime import datetime
        return datetime.now().strftime("%H%M%S")