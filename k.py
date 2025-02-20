import os
import json
import re
import asyncio
import aiohttp
import time
import logging
from typing import Dict, Optional

# Path to store the appstate
COOKIE_PATH = '/storage/emulated/0/a/appstate.txt'

class FacebookAutoShare:
    def __init__(self):
        self.sessions_dir = "fb_sessions"
        self.total: Dict[str, Dict] = {}
        self.fb_url_pattern = re.compile(r'^https:\/\/(?:www\.)?facebook\.com\/(?:(?:\w+\/)*\d+\/posts\/\d+\/\??(?:app=fbl)?|share\/(?:p\/)?[a-zA-Z0-9]+\/?)')
        
        os.makedirs(self.sessions_dir, exist_ok=True)
        self.load_sessions()
        
        logging.basicConfig(level=logging.INFO, 
                            format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def load_sessions(self):
        try:
            for file in os.listdir(self.sessions_dir):
                with open(os.path.join(self.sessions_dir, file), 'r') as f:
                    session_data = json.load(f)
                    self.total[session_data['id']] = session_data
        except Exception as e:
            self.logger.error(f"Error loading sessions: {str(e)}")

    def save_cookie(self, cookie_str: str):
        try:
            with open(COOKIE_PATH, 'w') as f:
                f.write(cookie_str)
        except Exception as e:
            self.logger.error(f"Error saving cookie: {str(e)}")

    def load_cookie(self) -> Optional[str]:
        try:
            if os.path.exists(COOKIE_PATH):
                with open(COOKIE_PATH, 'r') as f:
                    return f.read().strip()
            return None
        except Exception as e:
            self.logger.error(f"Error loading cookie: {str(e)}")
            return None

    async def share_post(self, cookies: str, url: str, amount: int, interval: int):
        async with aiohttp.ClientSession() as session:
            headers = {'cookie': cookies}
            shared_count = 0
            
            while shared_count < amount:
                try:
                    async with session.post(f"https://graph.facebook.com/me/feed?link={url}&published=0", headers=headers) as response:
                        if response.status == 200:
                            shared_count += 1
                            self.logger.info(f"Shared {shared_count}/{amount}")
                    await asyncio.sleep(interval)
                except Exception as e:
                    self.logger.error(f"Error sharing post: {str(e)}")
                    break

async def main():
    fb_share = FacebookAutoShare()
    
    print("=== Facebook Auto Share Tool ===")
    cookie = fb_share.load_cookie()
    
    if not cookie:
        cookie = input("Enter Facebook cookies (JSON format): ")
        fb_share.save_cookie(cookie)
    
    url = input("Enter Facebook post URL: ")
    amount = int(input("Enter number of shares: "))
    interval = int(input("Enter interval between shares (seconds): "))
    
    try:
        cookies = cookie.strip()
        await fb_share.share_post(cookies, url, amount, interval)
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
