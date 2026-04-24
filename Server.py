#!/usr/bin/env python3
"""
NullReader Server Engine v0.1.0
- RAM-buffered file serving
- Smart Browser & LAN IP detection
- Persistent UI Dashboard (Press 'i' to refresh)
"""

import http.server
import socketserver
import json
import os
import time
import sys
import webbrowser
import socket
import threading
from threading import Timer
from pathlib import Path
import urllib.request

if os.name == 'nt':
    import msvcrt
    import winreg

# --- TERMINAL STYLING ---
C_BLUE = "\033[94m"
C_CYAN = "\033[96m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_RED = "\033[91m"
C_GRAY = "\033[90m"
C_BOLD = "\033[1m"
C_END = "\033[0m"

PORT = 8080
VERSION = "v0.1.0"
READ_STATUS_FILE = 'readStatus.json'
PREFS_FILE = 'preferences.json'

# --- UI ASSETS ---
BIG_NUMS = {
    '3': [" 3333 ", "33  33", "   333", "33  33", " 3333 "],
    '2': [" 2222 ", "22 22", "  22  ", " 22   ", "222222"],
    '1': ["1111  ", "  11  ", "  11  ", "  11  ", "111111"]
}

ASCII_LOGO = (
    f"{C_CYAN}{C_BOLD}" + r"    _   __      ____ __                  __           " + "\n" +
    f"{C_CYAN}{C_BOLD}" + r"   / | / /_  __/ / / __ \ ___  ___  __ _/ /__  _____ " + "\n" +
    f"{C_BLUE}{C_BOLD}" + r"  /  |/ / / / / / / /_/ / _ \/ __ \/ __  / _ \/ ___/ " + "\n" +
    f"{C_BLUE}{C_BOLD}" + r" / /|  / /_/ / / / _, _/  __/ /_/ / /_/ /  __/ /     " + "\n" +
    f"{C_BLUE}{C_BOLD}" + r"/_/ |_/\__,_/_/_/_/ |_|\___/_/ /_/\__,_/\___/_/      " + f"{C_END}"
)

# --- Version Check ---
def check_for_updates():
    """Fetches latest release tag from GitHub API without external dependencies"""
    url = "https://api.github.com/repos/broveer/NullReader/releases"
    try:
        # GitHub API requires a User-Agent header
        req = urllib.request.Request(url, headers={'User-Agent': 'NullReader-App'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            if data and isinstance(data, list):
                # The first item in the list is the latest release
                latest_tag = data[0].get("tag_name", "")
                if latest_tag and latest_tag != VERSION:
                    return latest_tag
    except Exception:
        # Silently fail if offline or API is down
        pass
    return None

# --- UTILITY FUNCTIONS ---

def load_prefs():
    default_prefs = {"theme": "default.css", "show_qr": True, "hide_ip": False}
    if os.path.exists(PREFS_FILE):
        try:
            with open(PREFS_FILE, 'r') as f:
                return {**default_prefs, **json.load(f)}
        except: pass
    return default_prefs

def get_browser_name():
    """Identifies the default browser via Windows Registry"""
    if os.name != 'nt': return "MacOS/Linux Default"
    try:
        path = r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\http\UserChoice"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path) as key:
            prog_id = winreg.QueryValueEx(key, "ProgId")[0]
        
        if "Chrome" in prog_id: return "Google Chrome"
        if "Firefox" in prog_id: return "Mozilla Firefox"
        if "MSEdge" in prog_id: return "Microsoft Edge"
        if "Comet" in prog_id or "Perplexity" in prog_id: return "Comet"
        return prog_id.split('.')[-1] if '.' in prog_id else prog_id
    except:
        return "System Default"

def get_local_ip():
    """Finds the LAN IP address (e.g. 192.168.x.x) for mobile reading"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def show_info_panel():
    """Displays the system dashboard"""
    ip = get_local_ip()
    network_url = f"http://{ip}:{PORT}"
    browser = get_browser_name()
    prefs = load_prefs()
    print(f" {C_GREEN}🚀{C_END} {C_BOLD}STATUS:{C_END}     {C_GREEN}Online{C_END}")
    print(f" {C_BLUE}🔗{C_END} {C_BOLD}LOCAL:{C_END}      {C_CYAN}http://localhost:{PORT}{C_END}")
    if prefs.get("hide_ip"):
        print(f" {C_BLUE}📱{C_END} {C_BOLD}NETWORK:{C_END}    {C_GRAY}[ Hidden by Preferences ]{C_END}")
    else:
        print(f" {C_BLUE}📱{C_END} {C_BOLD}NETWORK:{C_END}    {C_CYAN}{network_url}{C_END}")
    print(f" {C_CYAN}🌐{C_END} {C_BOLD}BROWSER:{C_END}    {C_BOLD}{browser}{C_END}")
    print(f" {C_RED}🛑{C_END} {C_BOLD}STOP:{C_END}       Press {C_RED}Ctrl+C{C_END}")
    print(f" {C_YELLOW}⌨️ {C_END} {C_BOLD}INFO:{C_END}       Press {C_YELLOW}'i'{C_END} to refresh this dashboard")
    def update_alert_task():
        new_version = check_for_updates()
        if new_version:
            print(f" {C_YELLOW}✨{C_END} {C_BOLD}UPDATE:{C_END}     {C_YELLOW}New Version {new_version} available!{C_END}")
            print(f" {C_GRAY}│{C_END}           Download: https://github.com/broveer/NullReader/releases")
    threading.Thread(target=update_alert_task, daemon=True).start()
    print(f"{C_GRAY} ------------------------------------------------{C_END}")

def listen_for_keys():
    """Non-blocking keyboard listener for UI refresh"""
    while True:
        if os.name == 'nt' and msvcrt.kbhit():
            key = msvcrt.getch().decode('utf-8').lower()
            if key == 'i':
                os.system('cls' if os.name == 'nt' else 'clear')
                print(f"{C_GRAY}{ASCII_LOGO}{C_END}")
                print(f"           {C_GRAY}> Lightweight Comic Reader {C_GRAY}<")
                print(f"           {C_GRAY}> {C_END}{C_BOLD}SERVER ENGINE{C_END}{C_GRAY} | {C_END}{C_CYAN}{VERSION}{C_END} {C_GRAY}<")
                show_info_panel()
                print(f" {C_GRAY}Activity Log:{C_END}")
        time.sleep(0.1)

# --- SERVER HANDLER ---

class ComicReaderHandler(http.server.SimpleHTTPRequestHandler):
    
    def end_headers(self):
        """Cache-busting for library data"""
        if self.path.endswith('.js') or self.path.endswith('.json'):
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
        super().end_headers()

    def log_message(self, format, *args):
        """Aesthetic activity logging"""
        try:
            msg = str(args[0]) if args else ""
            status = str(args[1]) if len(args) > 1 else ""
            if any(x in msg for x in ["readStatus", "heartbeat", "favicon.ico"]):
                return
            
            color = C_GRAY
            if status.startswith('2'): color = C_GREEN
            elif status.startswith('4'): color = C_YELLOW
            elif status.startswith('5'): color = C_RED

            parts = msg.split(' ')
            method = f"{C_BOLD}{parts[0]}{C_END}"
            path = parts[1] if len(parts) > 1 else ""
            print(f" {C_GRAY}│{C_END}  {method.ljust(12)} {path.ljust(45)} {C_GRAY}→{C_END} {color}{status}{C_END}")
        except: pass

    def do_GET(self):
        if self.path == '/api/readstatus': self.serve_read_status()
        else: super().do_GET()
    
    def do_POST(self):
        if self.path == '/api/readstatus': self.update_read_status()
        elif self.path == '/api/saveconfig': self.save_config()
        else: self.send_error(404, 'Not Found')

    def serve_read_status(self):
        try:
            data = {}
            if os.path.exists(READ_STATUS_FILE):
                with open(READ_STATUS_FILE, 'r') as f: data = json.load(f)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode('utf-8'))
        except Exception as e: self.send_error(500, f'Error: {str(e)}')

    def update_read_status(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))
            with open(READ_STATUS_FILE, 'w') as f: json.dump(data, f, indent=2)
            self.send_success_response()
        except Exception as e: self.send_error(500, f'Error: {str(e)}')

    def save_config(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            payload = json.loads(body.decode('utf-8'))
            folder_path = payload.get('folder', '')
            if not folder_path or '..' in folder_path:
                self.send_error(400, 'Invalid folder')
                return
            config_file_path = os.path.join(folder_path, 'config.json')
            with open(config_file_path, 'w') as f: json.dump(payload.get('config', {}), f, indent=4)
            self.send_success_response()
        except Exception as e: self.send_error(500, f'Error: {str(e)}')

    def send_success_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(b'{"status": "ok"}')

# --- MAIN ---

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # 1. Header
    print(f"{C_GRAY} ------------------------------------------------{C_END}")
    print(f"{C_GRAY}{ASCII_LOGO}{C_END}")
    print(f"          {C_GRAY}>{C_END} Lightweight Comic Reader {C_END}{C_GRAY}<")
    print(f"           {C_GRAY}> {C_END}{C_BOLD}SERVER ENGINE{C_END}{C_GRAY} | {C_END}{C_CYAN}{VERSION}{C_END} {C_GRAY}<")
    print(f"{C_GRAY} ------------------------------------------------{C_END}")

    # 2. Big Countdown (Overwrites itself)
    for num in ['3', '2', '1']:
        for line in BIG_NUMS[num]:
            print(f"             {C_YELLOW}{line}{C_END}")
        time.sleep(1)
        sys.stdout.write("\033[5F\033[J") 
        sys.stdout.flush()

    # 3. Final Dashboard
    show_info_panel()
    print(f"\n {C_GRAY}Activity Log:{C_END}")

    # 4. Background Tasks
    Timer(1.0, lambda: webbrowser.open(f"http://localhost:{PORT}")).start()
    threading.Thread(target=listen_for_keys, daemon=True).start()

    # 5. Start Server
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), ComicReaderHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print(f"\n{C_RED} 🛑 Server stopped.{C_END}")