# Snapshot Feature for ShellMind AI Terminal

A comprehensive project state management and recovery system that provides AI-powered snapshots, automatic backups, and intelligent recovery capabilities.

## 🚀 Features

### 1. Workspace Snapshots
Save complete project state including files, dependencies, environment, and system information.

```bash
ai snapshot create before-refactor "Before major refactoring"
ai snapshot restore before-refactor
```

### 2. Instant Undo
Automatic snapshots before risky operations with one-command undo.

```bash
# After running: rm config.json
ai undo  # Restores the file
```

### 3. Debug Snapshots
Capture state before program execution for crash analysis.

```bash
ai run app.py  # Creates debug snapshot automatically
# If crash occurs:
ai debug crash-state
```

### 4. Snapshot Comparison
Compare project states with detailed change analysis.

```bash
ai snapshot diff before-update after-update
```

### 5. AI Smart Snapshots
AI automatically suggests and creates snapshots before risky operations.

### 6. System Snapshots
Capture system-level information (CPU, memory, processes, network).

```bash
ai snapshot system
```

### 7. Timeline View
See chronological history of all snapshots.

```bash
ai timeline
```

### 8. AI Suggestions
Get intelligent recommendations for when to create snapshots.

### 9. Snapshot Explorer
Browse, inspect, and manage all snapshots.

```bash
ai snapshot list
ai snapshot inspect before-refactor
```

### 10. One-Command Recovery
Automatically find and restore to the last stable state.

```bash
ai recover
```

## 📁 Project Structure

```
snapshot/
├── __init__.py              # Module initialization
├── models.py                # Data models for snapshots
├── storage.py               # File system storage handling
├── snapshot_manager.py      # Core snapshot creation/restoration
├── analyzer.py              # AI-powered analysis features
├── commands.py              # Command handlers
├── integration.py           # Integration guide
└── README.md               # This documentation
```

## 🛠️ Installation & Setup

1. **Install Dependencies:**
   ```bash
   pip install psutil
   ```

2. **Integrate into Main Project:**
   Follow the steps in `integration.py` to add snapshot commands to your terminal.

3. **Test Installation:**
   ```bash
   ai snapshot create test
   ai snapshot list
   ```

## 📖 Usage Guide

### Basic Operations

```bash
# Create snapshot
ai snapshot create my-snapshot "Optional description"

# List all snapshots
ai snapshot list

# Restore snapshot
ai snapshot restore my-snapshot

# Delete snapshot
ai snapshot delete my-snapshot
```

### Advanced Analysis

```bash
# Compare two snapshots
ai snapshot diff snapshot1 snapshot2

# Analyze single snapshot
ai snapshot analyze my-snapshot

# Inspect snapshot details
ai snapshot inspect my-snapshot
```

### Recovery & Undo

```bash
# Recover to last stable state
ai recover

# Undo last operation
ai undo

# View timeline
ai timeline
```

### System Operations

```bash
# Create system snapshot
ai snapshot system

# View storage statistics
ai snapshot stats
```

## 🔧 Configuration

### Storage Location
Snapshots are stored in `.snapshots/` directory in your project root.

### File Size Limits
- Maximum file size: 10MB per file
- Maximum files per snapshot: 1000
- Compressed storage using gzip

### Automatic Snapshots
Triggered before:
- File deletions (`rm`, `del`)
- Package installations (`pip install`, `npm install`)
- Git operations (`git pull`, `git merge`)
- Program execution (`python`, `node`)

## 🧠 AI Features

### Smart Analysis
- Detects risk levels of changes
- Identifies potential breaking changes
- Suggests testing strategies

### Anomaly Detection
- Large file warnings
- High CPU/memory usage alerts
- Uncommitted change monitoring

### Intelligent Suggestions
- Recommends snapshots before risky operations
- Provides recovery recommendations
- Analyzes change patterns

## 📊 Data Captured

### Files
- Content (text files only)
- Metadata (size, modification time)
- File paths and structure

### System
- CPU usage
- Memory usage
- Disk space
- Network connections

### Processes
- Running processes
- CPU/memory per process
- Process commands

### Dependencies
- Python packages (pip)
- Node.js packages (npm)
- System packages

### Environment
- Environment variables
- Python/Node versions
- Working directory

### Git
- Current branch
- Repository status
- Uncommitted changes
- Staged files

## 🚨 Safety & Security

- Sensitive environment variables are filtered out
- Large binary files are excluded
- Automatic compression reduces storage usage
- Risk assessment for all operations

## 🔄 Integration Points

The snapshot system integrates with:
- Command execution pipeline
- Error handling system
- Git operations
- Package management
- System monitoring

## 🐛 Troubleshooting

### Common Issues

1. **Permission Errors**
   - Ensure write access to project directory
   - Check file system permissions

2. **Large Projects**
   - Increase file size limits in `snapshot_manager.py`
   - Exclude unnecessary directories

3. **Storage Issues**
   - Monitor disk space usage
   - Clean up old snapshots regularly

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🤝 Contributing

1. Follow the existing code structure
2. Add tests for new features
3. Update documentation
4. Ensure backward compatibility

## 📄 License

This feature is part of the ShellMind AI Terminal project.

---

## 🎯 Quick Start

1. Integrate the feature (see `integration.py`)
2. Create your first snapshot: `ai snapshot create welcome`
3. Explore features: `ai snapshot list`
4. Try recovery: `ai recover`

The snapshot system will automatically create backups for risky operations and provide AI-powered insights into your project changes.