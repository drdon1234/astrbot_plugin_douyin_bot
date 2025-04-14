import aiohttp
import asyncio
import re
import json
from datetime import datetime
from astrbot.api.message_components import Plain, Video, Node, Nodes

class DouyinParser:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 8.0.0; SM-G955U Build/R16NW) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36',
            'Referer': 'https://www.douyin.com/?is_from_mobile_home=1&recommend=1'
        }
        self.semaphore = asyncio.Semaphore(10)

    async def get_redirected_url(self, session, url):
        async with session.head(url, allow_redirects=True) as response:
            return str(response.url)

    async def fetch_video_info(self, session, video_id):
        url = f'https://www.iesdouyin.com/share/video/{video_id}/'
        try:
            async with session.get(url, headers=self.headers) as response:
                response_text = await response.text()
                data = re.findall(r'_ROUTER_DATA\s*=\s*(\{.*?\});', response_text)
                if data:
                    json_data = json.loads(data[0])
                    item_list = json_data['loaderData']['video_(id)/page']['videoInfoRes']['item_list'][0]
                    nickname = item_list['author']['nickname']
                    title = item_list['desc']
                    timestamp = datetime.fromtimestamp(item_list['create_time']).strftime('%Y-%m-%d')
                    video = item_list['video']['play_addr']['uri']
                    video_url = (
                        video if video.endswith(".mp3") else
                        video.split("video_id=")[-1] if video.startswith("https://") else
                        f'https://www.douyin.com/aweme/v1/play/?video_id={video}'
                    )
                    images = [image['url_list'][0] for image in item_list.get('images', []) if 'url_list' in image]
                    return {
                        'nickname': nickname,
                        'title': title,
                        'timestamp': timestamp,
                        'raw_url': url,
                        'video_url': video_url,
                        'images': images
                    }
                else:
                    return None
        except aiohttp.ClientError as e:
            print(f'请求错误：{e}')
            return None

    async def parse(self, session, url):
        async with self.semaphore:
            try:
                redirected_url = await self.get_redirected_url(session, url)
                match = re.search(r'(\d+)', redirected_url)
                if match:
                    video_id = match.group(1)
                    return await self.fetch_video_info(session, video_id)
                else:
                    return None
            except aiohttp.ClientError as e:
                return e

    @staticmethod
    def extract_video_links(input_text):
        douyin_video_pattern = r'https?://(?:www\.|v\.)?douyin\.com/(?:video/\d+|[^\s]+)'
        video_links = re.findall(douyin_video_pattern, input_text)
        return video_links

    async def build_nodes(self, event):
        try:
            input_text = event.message_str
            sender_name = "抖音bot"
            sender_id = int(event.get_self_id()) or 10000
            
            urls = self.extract_video_links(input_text)
            if not urls:
                return None
                
            nodes = []
            async with aiohttp.ClientSession() as session:
                tasks = [self.parse(session, url) for url in urls]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if result and not isinstance(result, Exception):
                        nodes.append(
                            Node(
                                name=sender_name,
                                uin=sender_id,
                                content=[
                                    Plain(f"标题：{result['title']}\n作者：{result['nickname']}\n发布时间：{result['timestamp']}")
                                ]
                            )
                        )
                        nodes.append(
                            Node(
                                name=sender_name,
                                uin=sender_id,
                                content=[
                                    Video.fromURL(result['video_url'])
                                ]
                            )
                        )
                        
            if not nodes:
                return None
                
            return nodes
        except Exception as e:
            print(f"构建节点时发生错误：{e}")
            return None

    async def parse_urls(self, input_text):
        urls = self.extract_video_links(input_text)
        async with aiohttp.ClientSession() as session:
            tasks = [self.parse(session, url) for url in urls]
            return await asyncio.gather(*tasks, return_exceptions=True)
