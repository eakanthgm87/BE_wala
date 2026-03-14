"""
Project Process Monitor - Shows only YOUR development projects
Tracks React, Node, Python, etc. with their ports
"""

import psutil
import os
import time
import re
from datetime import datetime
from typing import List, Dict

# Terminal colors
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


def is_system_process(name: str, cmdline: str, cwd: str) -> bool:
    """
    Check if a process is a system process (should be hidden)
    """
    system_keywords = [
        'system', 'windows', 'winlogon', 'services', 'svchost',
        'dwm', 'csrss', 'lsass', 'smss', 'runtimebroker',
        'securityhealth', 'sihost', 'taskhost', 'shellexperiencehost',
        'startmenuexperiencehost', 'searchapp', 'cortana',
        'system32', 'syswow64', 'ntoskrnl', 'wininit',
        'conhost', 'cmd.exe', 'powershell.exe'
    ]
    
    name_lower = name.lower()
    cmdline_lower = cmdline.lower()
    cwd_lower = cwd.lower()
    
    # Check by name
    for kw in system_keywords:
        if kw in name_lower:
            return True
    
    # Check by location (system directories)
    system_paths = [r'c:\windows', r'c:\program files', r'c:\program files (x86)']
    for path in system_paths:
        if path in cwd_lower:
            return True
    
    # Check for system commands
    system_cmds = ['conhost', 'cmd.exe', 'powershell']
    for cmd in system_cmds:
        if cmd in cmdline_lower:
            return True
    
    return False


def is_development_process(name: str, cmdline: str, cwd: str) -> bool:
    """
    Check if this is a development project we care about
    """
    name_lower = name.lower()
    cmdline_lower = cmdline.lower()
    cwd_lower = cwd.lower()
    
    # Development keywords that identify projects
    dev_keywords = [
        'node', 'npm', 'react', 'vite', 'webpack', 'next',
        'python', 'flask', 'django', 'fastapi', 'uvicorn',
        'java', 'spring', 'tomcat', 'jetty',
        'go', 'gin', 'fiber',
        'php', 'artisan', 'symfony', 'laravel',
        'ruby', 'rails', 'sinatra',
        'dotnet', 'iis', 'kestrel'
    ]
    
    # Check by name
    for kw in dev_keywords:
        if kw in name_lower:
            return True
    
    # Check by command line patterns
    dev_patterns = [
        'npm start', 'npm run', 'node ', 'nodemon',
        'python app.py', 'python manage.py', 'flask run',
        'uvicorn', 'gunicorn',
        'go run', './main', 
        'java -jar', 'mvn spring-boot:run',
        'dotnet run', 'php artisan serve',
        'react-scripts', 'vite', 'next dev',
        'python main.py', 'python script.py'
    ]
    
    for pattern in dev_patterns:
        if pattern in cmdline_lower:
            return True
    
    # Check if it's a Python script in your project directory
    if 'python' in name_lower and cwd and 'shellmind-ai-terminal' in cwd.lower():
        return True
    
    return False


def extract_port_from_cmdline(cmdline: str) -> List[int]:
    """
    Extract port numbers from command line arguments
    """
    ports = []
    
    port_patterns = [
        r'--port[=:](\d+)',
        r'-p[=:](\d+)',
        r':(\d+)',
        r'0\.0\.0\.0:(\d+)',
        r'localhost:(\d+)',
        r'127\.0\.0\.1:(\d+)',
        r'PORT=(\d+)',
    ]
    
    for pattern in port_patterns:
        matches = re.findall(pattern, cmdline, re.IGNORECASE)
        for match in matches:
            try:
                port = int(match)
                if 1024 <= port <= 65535:
                    ports.append(port)
            except:
                pass
    
    return list(set(ports))


def get_project_processes() -> List[Dict]:
    """
    Get all development-related processes including Python scripts
    FIXED: Removed 'connections' from process_iter attributes
    """
    projects = []
    current_pid = os.getpid()
    
    # Fixed: Removed 'connections' from the attributes list
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 
                                     'memory_info', 'create_time', 'username']):
        try:
            pinfo = proc.info
            pid = pinfo['pid']
            
            # Skip current terminal process
            if pid == current_pid:
                continue
            
            # Get process name and command line
            name = pinfo['name'] or ''
            cmdline = ' '.join(pinfo['cmdline'] or [])
            
            # Get working directory
            cwd = ""
            try:
                cwd = proc.cwd()
            except:
                cwd = "Unknown"
            
            # Skip system processes
            if is_system_process(name, cmdline, cwd):
                continue
            
            # Check if it's a development process
            if not is_development_process(name, cmdline, cwd):
                continue
            
            # Get ports from connections - FIXED: Use connections() method, not attribute
            ports = []
            try:
                connections = proc.connections(kind='inet')
                for conn in connections:
                    if conn.laddr and conn.status == 'LISTEN':
                        port = conn.laddr.port
                        if 1024 <= port <= 65535:
                            ports.append(port)
            except (psutil.AccessDenied, psutil.ZombieProcess):
                pass
            except Exception:
                pass
            
            # If no ports from connections, try to extract from command line
            if not ports:
                ports = extract_port_from_cmdline(cmdline)
            
            # Get memory in MB
            memory = 0
            if pinfo['memory_info']:
                memory = pinfo['memory_info'].rss / 1024 / 1024
            
            # Get CPU
            cpu = pinfo['cpu_percent'] or 0
            
            # Determine project type
            project_type = detect_project_type(name, cmdline)
            
            # Get project name from working directory
            project_name = extract_project_name(cwd, name, cmdline)
            
            # Get age
            create_time = datetime.fromtimestamp(pinfo['create_time'])
            age_min = (datetime.now() - create_time).total_seconds() / 60
            
            projects.append({
                'pid': pid,
                'name': name,
                'project_name': project_name,
                'project_type': project_type,
                'ports': ports,
                'cpu': round(cpu, 1),
                'memory': round(memory, 1),
                'cwd': cwd,
                'age_min': round(age_min, 1),
                'cmdline': cmdline[:200]
            })
            
        except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
            continue
    
    return projects


def detect_project_type(name: str, cmdline: str) -> str:
    """
    Detect the type of project based on name and command line
    """
    name_lower = name.lower()
    cmdline_lower = cmdline.lower()
    
    # Python (always show Python processes)
    if 'python' in name_lower:
        if 'flask' in cmdline_lower:
            return 'Flask'
        elif 'django' in cmdline_lower:
            return 'Django'
        elif 'fastapi' in cmdline_lower:
            return 'FastAPI'
        else:
            return 'Python'
    
    # React
    if 'react' in cmdline_lower or 'react-scripts' in cmdline_lower:
        return 'React'
    
    # Next.js
    if 'next' in cmdline_lower:
        return 'Next.js'
    
    # Node.js/Express
    if 'node' in name_lower or 'npm' in name_lower:
        if 'express' in cmdline_lower:
            return 'Express'
        return 'Node.js'
    
    # Go
    if 'go' in name_lower:
        return 'Go'
    
    # Java
    if 'java' in name_lower:
        if 'spring' in cmdline_lower:
            return 'Spring Boot'
        return 'Java'
    
    return 'Dev Script'


def extract_project_name(cwd: str, default_name: str, cmdline: str) -> str:
    """
    Extract a meaningful project name from the working directory
    """
    if cwd and cwd != "Unknown":
        parts = cwd.split(os.sep)
        
        # Skip common system paths
        skip_folders = ['Windows', 'System32', 'Program Files', 'Program Files (x86)']
        
        for part in reversed(parts):
            if part and part not in skip_folders:
                if len(part) > 3:
                    return part
    
    # Clean up process name
    name = default_name.replace('.exe', '').replace('.EXE', '')
    return name


def format_projects_table(projects: List[Dict]) -> str:
    """
    Format projects in a beautiful table - SHOW ALL PROJECTS
    """
    if not projects:
        return f"\n{YELLOW}🚫 No development projects running.{RESET}\n"
    
    output = []
    output.append(f"\n{BRIGHT}{CYAN}═══════════════════════════════════════════════════════════════{RESET}")
    output.append(f"{BRIGHT}{CYAN}              🚀 YOUR DEVELOPMENT PROJECTS{RESET}")
    output.append(f"{BRIGHT}{CYAN}═══════════════════════════════════════════════════════════════{RESET}\n")
    
    # Table header
    output.append(f"{BRIGHT}{'PID':<8} {'Type':<12} {'Port':<8} {'Memory':<10} {'Project Name':<30}{RESET}")
    output.append(f"{BLUE}{'─'*80}{RESET}")
    
    for proj in sorted(projects, key=lambda x: x['project_name']):
        # Show port if available
        port_str = str(proj['ports'][0]) if proj['ports'] else '-'
        if proj['ports'] and len(proj['ports']) > 1:
            port_str += f" (+{len(proj['ports'])-1})"
        
        # Color based on memory
        mem_color = GREEN
        if proj['memory'] > 500:
            mem_color = RED
        elif proj['memory'] > 200:
            mem_color = YELLOW
        
        # Color based on type
        if proj['project_type'] == 'React':
            type_color = MAGENTA
        elif proj['project_type'] in ['Node.js', 'Express']:
            type_color = GREEN
        elif proj['project_type'] in ['Python', 'Flask', 'Django']:
            type_color = YELLOW
        else:
            type_color = CYAN
        
        proj_name = proj['project_name'][:30] if len(proj['project_name']) > 30 else proj['project_name']
        
        output.append(
            f"{proj['pid']:<8} "
            f"{type_color}{proj['project_type']:<12}{RESET} "
            f"{port_str:<8} "
            f"{mem_color}{proj['memory']:<10.1f}{RESET} "
            f"{proj_name}"
        )
    
    output.append(f"{BLUE}{'─'*80}{RESET}\n")
    
    # Summary
    total_memory = sum(p['memory'] for p in projects)
    projects_with_ports = [p for p in projects if p['ports']]
    
    output.append(f"{CYAN}📊 Total Projects: {len(projects)} | Total Memory: {total_memory:.0f}MB | With Ports: {len(projects_with_ports)}{RESET}")
    
    # URLs for projects with ports
    if projects_with_ports:
        output.append(f"\n{BRIGHT}{GREEN}🌐 Access URLs:{RESET}")
        for proj in projects_with_ports[:5]:
            port = proj['ports'][0]
            output.append(f"   • http://localhost:{port}  ({proj['project_name']})")
    
    return '\n'.join(output)


def format_projects_detailed(projects: List[Dict]) -> str:
    """Detailed view with more information"""
    if not projects:
        return f"\n{YELLOW}No development projects running.{RESET}\n"
    
    output = []
    output.append(f"\n{BRIGHT}{CYAN}═══════════════════════════════════════════════════════════════{RESET}")
    output.append(f"{BRIGHT}{CYAN}              🔍 DETAILED PROJECT INFORMATION{RESET}")
    output.append(f"{BRIGHT}{CYAN}═══════════════════════════════════════════════════════════════{RESET}\n")
    
    for proj in projects:
        type_color = MAGENTA if proj['project_type'] == 'React' else GREEN
        
        output.append(f"{BRIGHT}{type_color}📁 {proj['project_name']}{RESET}")
        output.append(f"{BLUE}  ┌{'─'*50}{RESET}")
        
        output.append(f"  │ {BRIGHT}Type:{RESET}     {proj['project_type']}")
        output.append(f"  │ {BRIGHT}PID:{RESET}      {proj['pid']}")
        
        if proj['ports']:
            output.append(f"  │ {BRIGHT}Port:{RESET}     {proj['ports'][0]}")
            output.append(f"  │ {BRIGHT}URL:{RESET}     http://localhost:{proj['ports'][0]}")
        
        mem_color = GREEN if proj['memory'] < 200 else YELLOW if proj['memory'] < 500 else RED
        output.append(f"  │ {BRIGHT}Memory:{RESET}   {mem_color}{proj['memory']}MB{RESET}")
        
        cpu_color = GREEN if proj['cpu'] < 30 else YELLOW if proj['cpu'] < 70 else RED
        output.append(f"  │ {BRIGHT}CPU:{RESET}      {cpu_color}{proj['cpu']}%{RESET}")
        
        output.append(f"  │ {BRIGHT}Runtime:{RESET}  {proj['age_min']} minutes")
        output.append(f"{BLUE}  └{'─'*50}{RESET}\n")
    
    return '\n'.join(output)


def stop_project(target: str) -> str:
    """Stop a project by name or PID"""
    projects = get_project_processes()
    target_proj = None
    
    # Find by PID
    if target.isdigit():
        pid = int(target)
        target_proj = next((p for p in projects if p['pid'] == pid), None)
    else:
        # Find by project name
        target_lower = target.lower()
        matches = [p for p in projects if target_lower in p['project_name'].lower()]
        
        if len(matches) == 1:
            target_proj = matches[0]
        elif len(matches) > 1:
            print(f"\n{YELLOW}Multiple projects found:{RESET}")
            for i, proj in enumerate(matches, 1):
                print(f"  {i}. {proj['project_name']} (PID: {proj['pid']})")
            
            choice = input(f"\n{BRIGHT}Select number (or 'c' to cancel):{RESET} ").strip()
            if choice.lower() == 'c':
                return "❌ Cancelled."
            
            if choice.isdigit() and 1 <= int(choice) <= len(matches):
                target_proj = matches[int(choice)-1]
    
    if not target_proj:
        return f"❌ No running project found matching '{target}'"
    
    # Confirm
    confirm = input(f"\n{RED}Stop {target_proj['project_name']}? (y/n): {RESET}").strip().lower()
    if confirm != 'y':
        return "❌ Cancelled."
    
    # Stop the process
    try:
        proc = psutil.Process(target_proj['pid'])
        proc.terminate()
        
        try:
            proc.wait(timeout=3)
            return f"\n{GREEN}✅ Project '{target_proj['project_name']}' stopped{RESET}"
        except psutil.TimeoutExpired:
            proc.kill()
            return f"\n{GREEN}✅ Project '{target_proj['project_name']}' killed{RESET}"
            
    except psutil.NoSuchProcess:
        return f"{RED}❌ Project already stopped{RESET}"
    except Exception as e:
        return f"{RED}❌ Error: {e}{RESET}"


def monitor_projects():
    """Live monitor for projects"""
    print(f"\n{CYAN}{BRIGHT}📈 LIVE PROJECT MONITOR{RESET}")
    print(f"{YELLOW}Press Ctrl+C to stop{RESET}\n")
    
    try:
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            
            projects = get_project_processes()
            
            if not projects:
                print(f"{YELLOW}No development projects running.{RESET}")
            else:
                print(f"{BRIGHT}{CYAN}🚀 Running Projects{RESET}")
                print(f"{BLUE}{'─'*80}{RESET}")
                print(f"{BRIGHT}{'PID':<8} {'Type':<12} {'Port':<8} {'CPU%':<8} {'Memory':<10} {'Project':<30}{RESET}")
                print(f"{BLUE}{'─'*80}{RESET}")
                
                for proj in projects:
                    type_color = MAGENTA if proj['project_type'] == 'React' else GREEN
                    cpu_color = GREEN if proj['cpu'] < 30 else YELLOW if proj['cpu'] < 70 else RED
                    mem_color = GREEN if proj['memory'] < 200 else YELLOW if proj['memory'] < 500 else RED
                    
                    port = str(proj['ports'][0]) if proj['ports'] else '-'
                    name = proj['project_name'][:30]
                    
                    print(
                        f"{proj['pid']:<8} "
                        f"{type_color}{proj['project_type']:<12}{RESET} "
                        f"{port:<8} "
                        f"{cpu_color}{proj['cpu']:<8.1f}{RESET} "
                        f"{mem_color}{proj['memory']:<10.1f}{RESET} "
                        f"{name}"
                    )
                
                print(f"{BLUE}{'─'*80}{RESET}")
                print(f"{CYAN}Total: {len(projects)} projects{RESET}")
            
            print(f"\n{YELLOW}Press Ctrl+C to exit{RESET}")
            time.sleep(2)
            
    except KeyboardInterrupt:
        print(f"\n\n{GREEN}✅ Monitor stopped{RESET}")


# ========== MAIN HANDLER FUNCTION ==========
def handle_project_command(args: list) -> str:
    """
    Main entry point for 'ai project' command
    This function is called from repl.py
    """
    if not args or args[0] == "list":
        projects = get_project_processes()
        return format_projects_table(projects)
    
    elif args[0] == "details":
        projects = get_project_processes()
        return format_projects_detailed(projects)
    
    elif args[0] == "stop" and len(args) > 1:
        return stop_project(' '.join(args[1:]))
    
    elif args[0] == "monitor":
        monitor_projects()
        return ""
    
    else:
        return f"""
{BRIGHT}{CYAN}Project Monitor - Commands:{RESET}
  {GREEN}ai project list{RESET}        - Show your running projects
  {GREEN}ai project details{RESET}     - Show detailed project info
  {GREEN}ai project stop <name>{RESET} - Stop a project
  {GREEN}ai project monitor{RESET}     - Live project monitor

Examples:
  ai project list
  ai project stop my-react-app
  ai project monitor
"""