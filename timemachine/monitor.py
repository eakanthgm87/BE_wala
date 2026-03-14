"""
Real-time File Monitor - Shows live file changes
"""

import time
from .core import get_timemachine

def start_monitor(interval=2):
    """Start real-time file change monitor"""
    tm = get_timemachine()
    print(f"{GREEN}🔍 Watching for file changes... (Ctrl+C to stop){RESET}")
    
    try:
        while True:
            changes = tm.check_file_changes()
            if changes:
                print(f"\n{GREEN}📁 Changes detected:{RESET}")
                for change in changes:
                    print(f"  {change[0]}: {change[1]}")
            time.sleep(interval)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}⏹️ Monitor stopped{RESET}")