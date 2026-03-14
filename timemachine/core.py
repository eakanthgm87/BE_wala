"""
Core Time Machine - Records EVERYTHING
"""

import os
import json
import time
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import threading

# Colors
try:
    import colorama
    colorama.init()
    GREEN = colorama.Fore.GREEN
    YELLOW = colorama.Fore.YELLOW
    RED = colorama.Fore.RED
    BLUE = colorama.Fore.BLUE
    CYAN = colorama.Fore.CYAN
    MAGENTA = colorama.Fore.MAGENTA
    RESET = colorama.Fore.RESET
    BRIGHT = colorama.Style.BRIGHT
except ImportError:
    GREEN = YELLOW = RED = BLUE = CYAN = MAGENTA = RESET = BRIGHT = ''


class TimeMachine:
    """Records EVERYTHING - commands, files, thoughts, git"""
    
    def __init__(self):
        self.home = Path.home()
        self.db_file = self.home / '.timemachine_complete.json'
        self.snapshots_dir = self.home / '.timemachine_snapshots'
        self.snapshots_dir.mkdir(exist_ok=True)
        
        self.data = self.load()
        self.last_files = {}
        self.watching = True
        
        # Start file watcher
        self.start_watcher()
    
    def load(self):
        """Load history from file"""
        if self.db_file.exists():
            try:
                with open(self.db_file, 'r') as f:
                    return json.load(f)
            except:
                return {'timeline': [], 'files': {}, 'branches': {}}
        return {'timeline': [], 'files': {}, 'branches': {}}
    
    def save(self):
        """Save history to file"""
        try:
            # Keep last 1000 timeline entries
            self.data['timeline'] = self.data['timeline'][-1000:]
            with open(self.db_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except:
            pass
    
    def get_git_branch(self):
        """Get current git branch"""
        try:
            r = subprocess.run(['git', 'branch', '--show-current'], 
                              capture_output=True, text=True)
            return r.stdout.strip() or 'main'
        except:
            return 'unknown'
    
    def get_file_hash(self, filepath):
        """Get MD5 hash of file"""
        try:
            with open(filepath, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()[:8]
        except:
            return None
    
    def snapshot_file(self, filepath):
        """Save a copy of file"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = Path(filepath).name
            snapshot_path = self.snapshots_dir / f"{filename}_{timestamp}"
            import shutil
            shutil.copy2(filepath, snapshot_path)
            return str(snapshot_path)
        except:
            return None
    
    def record(self, event_type, data, thought=None):
        """Record ANY event"""
        moment = {
            'id': hashlib.md5(str(time.time()).encode()).hexdigest()[:6],
            'time': time.time(),
            'time_str': datetime.now().strftime('%H:%M:%S'),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'type': event_type,  # 'command', 'file', 'thought', 'git'
            'data': data[:200] if isinstance(data, str) else data,
            'thought': thought,
            'path': os.getcwd(),
            'branch': self.get_git_branch()
        }
        
        self.data['timeline'].append(moment)
        self.save()
        return moment
    
    def scan_files(self):
        """Scan all files in current directory"""
        current_files = {}
        
        for root, dirs, files in os.walk('.'):
            # Skip junk directories
            dirs[:] = [d for d in dirs if d not in [
                '.git', '__pycache__', 'node_modules', 'venv', 'env'
            ]]
            
            for file in files:
                filepath = os.path.join(root, file)
                try:
                    stat = os.stat(filepath)
                    file_hash = self.get_file_hash(filepath)
                    current_files[filepath] = {
                        'hash': file_hash,
                        'mtime': stat.st_mtime,
                        'size': stat.st_size,
                        'path': filepath
                    }
                except:
                    pass
        
        return current_files
    
    def check_file_changes(self):
        """Check for file changes since last scan"""
        current = self.scan_files()
        changes = []
        
        # Check for new/modified files
        for filepath, info in current.items():
            if filepath not in self.last_files:
                # New file
                self.record('file', f"✅ Created: {filepath}")
                changes.append(('created', filepath))
                self.snapshot_file(filepath)
                
            elif info['hash'] != self.last_files[filepath]['hash']:
                # Modified file
                self.record('file', f"📝 Modified: {filepath}")
                changes.append(('modified', filepath))
                self.snapshot_file(filepath)
        
        # Check for deleted files
        for filepath in self.last_files:
            if filepath not in current:
                self.record('file', f"❌ Deleted: {filepath}")
                changes.append(('deleted', filepath))
        
        self.last_files = current
        return changes
    
    def start_watcher(self):
        """Start background file watcher"""
        def watcher():
            while self.watching:
                self.check_file_changes()
                time.sleep(3)  # Check every 3 seconds
        
        thread = threading.Thread(target=watcher, daemon=True)
        thread.start()
    
    def search(self, query):
        """Search through all history"""
        results = []
        query = query.lower()
        
        for m in self.data['timeline']:
            data_str = str(m.get('data', '')).lower()
            thought_str = str(m.get('thought', '')).lower()
            
            if (query in m['time_str'].lower() or
                query in data_str or
                query in thought_str):
                results.append(m)
        
        return results[-20:]  # Last 20 matches
    
    def get_timeline(self, days=7):
        """Get timeline from last X days"""
        now = time.time()
        cutoff = now - (days * 86400)  # days to seconds
        return [m for m in self.data['timeline'] if m['time'] > cutoff]
    
    def get_file_history(self, filepath):
        """Get history of a specific file"""
        history = []
        for m in self.data['timeline']:
            if m['type'] == 'file' and filepath in m.get('data', ''):
                history.append(m)
        return history


# Global instance
_machine = None

def get_timemachine():
    global _machine
    if _machine is None:
        _machine = TimeMachine()
    return _machine