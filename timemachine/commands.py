"""
Time Machine Commands
"""

import time
from .core import get_timemachine

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


def record_moment(command, output=""):
    """Record a command in the time machine"""
    tm = get_timemachine()
    tm.record('command', command)
    return True


def add_thought(thought):
    """Save a thought"""
    tm = get_timemachine()
    tm.record('thought', '', thought)
    return f"{GREEN}✅ Thought saved: '{thought}'{RESET}"


def track_file_changes():
    """Manually check file changes"""
    tm = get_timemachine()
    changes = tm.check_file_changes()
    if changes:
        print(f"{GREEN}📁 File changes detected:{RESET}")
        for c in changes[-5:]:
            print(f"  {c[0]}: {c[1]}")
    return changes


def show_timeline(hours=24):
    """Show recent history"""
    tm = get_timemachine()
    moments = tm.get_timeline(hours)
    
    if not moments:
        return f"{YELLOW}⚠️ No activity in last {hours} hours{RESET}"
    
    out = []
    out.append(f"\n{BRIGHT}{CYAN}📅 TIMELINE - Last {hours} hours{RESET}")
    out.append(f"{BLUE}{'─'*50}{RESET}")
    
    for m in moments[-30:]:
        if m['type'] == 'command':
            icon = "💻"
        elif m['type'] == 'file':
            if 'Created' in m['data']:
                icon = "✅"
            elif 'Modified' in m['data']:
                icon = "📝"
            elif 'Deleted' in m['data']:
                icon = "❌"
            else:
                icon = "📁"
        else:
            icon = "🧠"
        
        out.append(f"  {icon} {m['time_str']} {m['data']}")
        if m['thought']:
            out.append(f"     💭 {m['thought']}")
    
    return '\n'.join(out)


def time_travel(query):
    """Find a moment in time"""
    tm = get_timemachine()
    results = tm.search(query)
    
    if not results:
        return f"{YELLOW}⚠️ No moments found matching '{query}'{RESET}"
    
    m = results[0]
    out = []
    out.append(f"\n{BRIGHT}{CYAN}🌀 TIME TRAVEL - {m['date']} {m['time_str']}{RESET}")
    out.append(f"{BLUE}{'─'*40}{RESET}")
    out.append(f"📍 {m['path']}")
    out.append(f"🌿 {m['branch']}")
    out.append(f"📋 {m['data']}")
    if m['thought']:
        out.append(f"💭 {m['thought']}")
    
    return '\n'.join(out)


def whats_if(idea):
    """Save an alternate timeline idea"""
    tm = get_timemachine()
    tm.record('thought', f"✨ What if: {idea}")
    return f"{GREEN}✅ Parallel timeline created: '{idea}'{RESET}"


def show_file_history(filepath):
    """Show history of a specific file"""
    tm = get_timemachine()
    history = []
    for m in tm.data['timeline']:
        if m['type'] == 'file' and filepath in m['data']:
            history.append(m)
    
    if not history:
        return f"{YELLOW}⚠️ No history found for {filepath}{RESET}"
    
    out = []
    out.append(f"\n{BRIGHT}{CYAN}📁 FILE HISTORY: {filepath}{RESET}")
    out.append(f"{BLUE}{'─'*40}{RESET}")
    for m in history[-10:]:
        out.append(f"  {m['time_str']} {m['data']}")
    return '\n'.join(out)


def compare_files(file1, file2=None):
    """Compare file versions"""
    return f"{CYAN}🔍 Compare feature coming soon{RESET}"


def restore_file(filepath, time_ref=None):
    """Restore file from past"""
    return f"{CYAN}⏳ Restore feature coming soon{RESET}"