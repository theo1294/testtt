import os
import json
import re
import asyncio
import aiohttp
import time
import logging
from typing import Dict, Optional

COOKIE_PATH = '/storage/emulated/0/a/appstate.txt'

class FacebookAutoShare:
    def __init__(self):
        self.sessions_dir = "fb_sessions"
        self.total: Dict[str, Dict] = {}
        self.fb_url_pattern = re.compile(r'^https:\/\/(?:www\.)?facebook\.com\/(?:(?:\w+\/)*\d+\/posts\/\d+\/?\??(?:app=fbl)?|share\/(?:p\/)?[a-zA-Z0-9]+\/?)')
        
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

    def read_cookie_from_file(self) -> str:
        try:
            with open(COOKIE_PATH, 'r') as file:
                return file.read().strip()
        except Exception as e:
            self.logger.error(f"Error reading cookie file: {str(e)}")
            return ""

    async def get_access_token(self, cookie: str, session: aiohttp.ClientSession) -> Optional[str]:
        try:
            headers = {
                'authority': 'business.facebook.com',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'cookie': cookie,
                'referer': 'https://www.facebook.com/'
            }
            
            async with session.get('https://business.facebook.com/content_management', headers=headers) as response:
                text = await response.text()
                token_match = re.search(r'"accessToken":\s*"([^"]+)"', text)
                
                return token_match.group(1) if token_match else None
        except Exception as e:
            self.logger.error(f"Error getting access token: {str(e)}")
            return None

    async def share_post(self, url: str, amount: int, interval: int):
        cookie_str = self.read_cookie_from_file()
        if not cookie_str:
            self.logger.error("No valid cookie found in file.")
            return
        
        async with aiohttp.ClientSession() as session:
            access_token = await self.get_access_token(cookie_str, session)
            if not access_token:
                self.logger.error("Failed to get access token")
                return
            
            shared_count = 0
            while shared_count < amount:
                try:
                    async with session.post(
                        f"https://graph.facebook.com/me/feed?link={url}&published=0&access_token={access_token}"
                    ) as response:
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
    url = input("Enter Facebook post URL: ")
    amount = int(input("Enter number of shares: "))
    interval = int(input("Enter interval between shares (seconds): "))

    if not fb_share.fb_url_pattern.match(url):
        print("Invalid Facebook URL")
        return

    await fb_share.share_post(url, amount, interval)

if __name__ == "__main__":
    asyncio.run(main())
