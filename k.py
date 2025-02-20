#!/usr/bin/env python3
import threading
import requests
import sys
import os
import time
import subprocess
from typing import List, Optional, Dict
import json
from datetime import datetime, timedelta
from rich.console import Console
from rich import print
from rich.panel import Panel
import re
import pytz
from pathlib import Path

console = Console()
os.system('clear' if os.name == 'posix' else 'cls')

# File paths
COOKIE_PATH = '/storage/emulated/0/a/cookie.txt'
GLOBAL_SHARE_COUNT_FILE = 'global_share_count.json'
KEYS_FILE = 'auth_keys.json'
LAST_KEY_FILE = 'last_key.txt'

# Default admin password hash (password: "password")
ADMIN_HASH = "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"

config = {
    'post': '',
    'cookies': [],
    'total_shares': 0,
    'target_shares': 0
}

def loading_animation(duration: int, message: str):
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    end_time = time.time() + duration
    i = 0
    while time.time() < end_time:
        print(f"\r{frames[i]} {message}", end="")
        time.sleep(0.1)
        i = (i + 1) % len(frames)
    print("\r" + " " * (len(message) + 2))

def update_tool():
    try:
        print(Panel("[white]Checking for updates...", 
            title="[bright_white]>> [Update Check] <<",
            width=65,
            style="bold bright_white"
        ))
        
        result = subprocess.run(['git', 'pull'], capture_output=True, text=True)
        
        if "Already up to date" in result.stdout:
            print(Panel("[green]Tool is already up to date!", 
                title="[bright_white]>> [Update Status] <<",
                width=65,
                style="bold bright_white"
            ))
            time.sleep(2)
        else:
            print(Panel("[green]Tool updated successfully!\n[yellow]Please restart the script.", 
                title="[bright_white]>> [Update Status] <<",
                width=65,
                style="bold bright_white"
            ))
            sys.exit(0)
    except Exception as e:
        print(Panel(f"[red]Update failed: {str(e)}", 
            title="[bright_white]>> [Error] <<",
            width=65,
            style="bold bright_white"
        ))
        time.sleep(2)

def banner():
    os.system('clear' if os.name == 'posix' else 'cls')

    print(Panel(
        r"""
[cyan]           ▀▀█▀▀ ░█─░█ ░█▀▀▀ ░█▀▀▀█ 
[cyan]           ─░█── ░█▀▀█ ░█▀▀▀ ░█──░█ 
[cyan]           ─░█── ░█─░█ ░█▄▄▄ ░█▄▄▄█
""",
        title="[green]●[yellow] Active [/]",
        width=65,
        style="bold bright_white",
    ))
    
    console.print(Panel(
        """[bold cyan]⚡ [bold green]Tool[/]: [bright_magenta]SpamShare[/]
[bold cyan]⚡ [bold green]Version[/]: [bright_yellow]1.0.0[/]
[bold cyan]⚡ [bold green]Dev[/]: [italic green]Theo Devcode[/]
[bold cyan]⚡ [bold green]Status[/]: [bold red]Cookie Mode[/]

[bold yellow]Welcome to SpamShare![/]
[italic green]A powerful tool designed for efficient sharing and management. Keep an eye out for future updates and new features![/]
[bold blue]Stay connected and enjoy using SpamShare for your needs.[/]""",
        title="[bold white on red] SYSTEM INFORMATION [/]",
        width=65,
        style="bold bright_white",
    ))

def show_main_menu():
    print(Panel("""[1] Start Share Process
[2] Exit""",
        title="[bright_white]>> [Main Menu] <<",
        width=65,
        style="bold bright_white"
    ))
    
    choice = console.input("[bright_white]Enter choice (1-2): ")
    
    if choice == "2":
        return False
    return True

class Stats:
    def __init__(self, total_cookies):
        self.success = [0] * total_cookies
        self.failed = [0] * total_cookies

    def update_success(self, index):
        self.success[index] += 1

    def update_failed(self, index):
        self.failed[index] += 1

class FacebookShare:
    def __init__(self, cookie, post_link, share_count, cookie_index, stats):
        self.cookie = cookie
        self.post_link = post_link
        self.share_count = share_count
        self.cookie_index = cookie_index
        self.stats = stats
        self.session = requests.Session()
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36',
            'sec-ch-ua': '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': "Android",
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'cookie': self.cookie
        }
        self.session.headers.update(self.headers)

    def get_token(self):
        try:
            response = self.session.get('https://business.facebook.com/content_management')
            token_match = re.search('EAAG(.*?)","', response.text)
            if token_match:
                return 'EAAG' + token_match.group(1)
            return None
        except Exception as e:
            print(f"Error getting token for cookie {self.cookie_index + 1}: {str(e)}")
            return None

    def share_post(self):
        token = self.get_token()
        if not token:
            self.stats.update_failed(self.cookie_index)
            return

        self.session.headers.update({
            'accept-encoding': 'gzip, deflate',
            'host': 'b-graph.facebook.com'
        })

        count = 0
        while count < self.share_count:
            try:
                response = self.session.post(
                    f'https://b-graph.facebook.com/me/feed?link=https://mbasic.facebook.com/{self.post_link}&published=0&access_token={token}'
                )
                data = response.json()
                
                if 'id' in data:
                    count += 1
                    self.stats.update_success(self.cookie_index)
                    
                    result = f"[yellow]⚡ [cyan]Share Progress : [green]{count}/{self.share_count}[/]"
                    console.print(Panel(result, title="[white on red] SHARE PROGRESS [/]", width=65, style="bold bright_white"))
                    
                else:
                    print(f"\nCookie {self.cookie_index + 1} is blocked or invalid!")
                    self.stats.update_failed(self.cookie_index)
                    break
                    
            except Exception as e:
                print(f"\nError sharing post with cookie {self.cookie_index + 1}: {str(e)}")
                self.stats.update_failed(self.cookie_index)
                break

class ShareStats:
    def __init__(self):
        self.success_count = 0
        self.failed_count = 0
        self.lock = threading.Lock()
        self.cookie_stats = {}

    def update_success(self, cookie_index):
        with self.lock:
            self.success_count += 1
            if cookie_index not in self.cookie_stats:
                self.cookie_stats[cookie_index] = {"success": 0, "failed": 0}
            self.cookie_stats[cookie_index]["success"] += 1

    def update_failed(self, cookie_index):
        with self.lock:
            self.failed_count += 1
            if cookie_index not in self.cookie_stats:
                self.cookie_stats[cookie_index] = {"success": 0, "failed": 0}
            self.cookie_stats[cookie_index]["failed"] += 1

def load_cookies():
    try:
        cookie_file = Path(COOKIE_PATH)
        if cookie_file.exists():
            with open(cookie_file, 'r') as f:
                cookies = [line.strip() for line in f if line.strip()]
            console.print(f"[green]Successfully loaded {len(cookies)} cookies from {COOKIE_PATH}")
            return cookies
        else:
            console.print(f"[red]Cookie file not found at {COOKIE_PATH}")
            console.print("[yellow]Creating directory structure...")
            os.makedirs(os.path.dirname(COOKIE_PATH), exist_ok=True)
            with open(cookie_file, 'w') as f:
                f.write("")
            console.print(f"[green]Created empty cookie file at {COOKIE_PATH}")
            console.print("[yellow]Please add your cookies to the file and run the script again")
            return None
    except Exception as e:
        console.print(f"[red]Error loading cookies: {str(e)}")
        return None

def main():
    try:
        banner()
        
        # Load cookies
        cookies = load_cookies()
        if not cookies:
            return
        
        while True:
            if not show_main_menu():
                break
            
            # Starting share process
            print("[yellow]Enter target post link to share: [/yellow]")
            post_link = console.input("[bright_white]Post Link: ")
            print("[yellow]Enter number of shares: [/yellow]")
            try:
                share_count = int(console.input("[bright_white]Number of Shares: "))
            except ValueError:
                print("[red]Please enter a valid number for share count!")
                continue

            stats = ShareStats()
            threads = []
            
            for i, cookie in enumerate(cookies):
                facebook_share = FacebookShare(cookie, post_link, share_count, i, stats)
                thread = threading.Thread(target=facebook_share.share_post)
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            print(f"\n[cyan]Sharing complete! Total successful shares: {stats.success_count}, Failed: {stats.failed_count}[/cyan]")
            print(f"[yellow]Total successful shares for each cookie:")
            for cookie_index, stats in stats.cookie_stats.items():
                print(f"Cookie {cookie_index + 1} -> Success: {stats['success']} / Failed: {stats['failed']}")

            # Proceed to menu again
            print("\n[green]Returning to menu...\n")
            
    except KeyboardInterrupt:
        console.print("\n[red]Exiting...")
        sys.exit(0)

if __name__ == '__main__':
    main()
    
