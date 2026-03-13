# Integration Guide for Snapshot Feature
# How to integrate the snapshot system into the main ShellMind AI Terminal

"""
INTEGRATION STEPS:

1. Add snapshot command handling to core/repl.py:

   In the main command loop, add this before the AI command generation:

   # ----------------------------------------------
   # SNAPSHOT COMMANDS
   # ----------------------------------------------
   if query.startswith("snapshot "):
       from snapshot.commands import SnapshotCommands

       parts = query.split()
       if len(parts) >= 2:
           subcommand = parts[1]
           args = parts[2:]
           cmd_handler = SnapshotCommands()
           result = cmd_handler.handle_command(subcommand, args)
           print(result)
           continue

2. Add auto-snapshot creation before risky operations:

   In the command execution section, add:

   # Check for auto-snapshot before risky operations
   from snapshot.snapshot_manager import SnapshotManager
   manager = SnapshotManager()
   auto_snap = manager.auto_snapshot(user_input)
   if auto_snap:
       print(f"📸 Auto-snapshot created: {auto_snap}")

3. Add snapshot suggestions:

   Before command execution, add:

   from snapshot.analyzer import SnapshotAnalyzer
   analyzer = SnapshotAnalyzer(manager)
   suggestion = analyzer.suggest_snapshots(user_input)
   if suggestion:
       print(suggestion)

4. For undo functionality, you can add:

   if query == "undo":
       from snapshot.commands import SnapshotCommands
       cmd_handler = SnapshotCommands()
       result = cmd_handler.cmd_undo()
       print(result)
       continue

USAGE EXAMPLES:

# Basic snapshots
ai snapshot create before-refactor
ai snapshot restore before-refactor
ai snapshot list
ai snapshot delete before-refactor

# Analysis and comparison
ai snapshot analyze before-refactor
ai snapshot diff before-update after-update

# System and recovery
ai snapshot system
ai snapshot recover
ai undo

# Timeline and inspection
ai snapshot timeline
ai snapshot inspect before-refactor

DEPENDENCIES:

The snapshot feature requires:
- psutil (for system monitoring)
- Install with: pip install psutil

OPTIONAL ENHANCEMENTS:

- Add compression for large snapshots
- Implement cloud storage for snapshots
- Add snapshot sharing/collaboration features
- Integrate with CI/CD pipelines

TESTING:

Run the snapshot commands in your terminal to test functionality.
The .snapshots/ directory will be created in your project root.
"""