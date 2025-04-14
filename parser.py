from astrbot.api.message_components import Plain, Video, Image, Node, Nodes
from datetime import datetime
import aiohttp
import asyncio
import re
import json

class DouyinParser:
    def __init__(self):
        self.app_pattern = re.compile(r'https?://v\.douyin\.com/[^\s]+')
        self.web_pattern = re.compile(r'https?://(?:www\.)?douyin\.com/[^\s]*?(\d{19})[^\s]*')
        self.router_data_pattern = re.compile(r'_ROUTER_DATA\s*=\s*(\{.*?\});')
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 8.0.0; SM-G955U Build/R16NW) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36',
            'Referer': 'https://www.douyin.com/?is_from_mobile_home=1&recommend=1'
        }
        self.semaphore = asyncio.Semaphore(10)

    async def build_nodes(self, event):
        try:
            input_text = event.message_str
            urls = self.extract_video_links(input_text)
            if not urls:
                return None
            nodes = []
            sender_name = "抖音bot"
            sender_id = int(event.get_self_id()) or 10000
            connector = aiohttp.TCPConnector(limit=self.semaphore._value)
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(connector=connector, timeout=timeout, headers=self.headers) as session:
                tasks = [self.parse(session, url) for url in urls]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    if result and not isinstance(result, Exception):
                        nodes.append(
                            Node(
                                name=sender_name,
                                uin=sender_id,
                                content=[Plain(f"标题：{result['title']}\n作者：{result['nickname']}\n发布时间：{result['timestamp']}")]
                            )
                        )
                        if result['is_gallery']:
                            for image_url in result['images']:
                                nodes.append(
                                    Node(
                                        name=sender_name,
                                        uin=sender_id,
                                        content=[Image.fromURL(image_url)]
                                    )
                                )
                        else:
                            nodes.append(
                                Node(
                                    name=sender_name,
                                    uin=sender_id,
                                    content=[Video.fromURL(result['video_url'])]
                                )
                            )
            return nodes if nodes else None
        except Exception:
            return None

    def extract_video_links(self, input_text):
        result_links = []
        mobile_links = self..findall(input_text)
        result_links.extend(mobile_links)
        web_matches = self.web_pattern.finditer(input_text)
        for match in web_matches:
            video_id = match.group(1)
            standardized_url = f"https://www.douyin.com/video/{video_id}"
            result_links.append(standardized_url)
        return result_links

    async def parse(self, session, url):
        for attempt in range(3):
            try:
                async with self.semaphore:
                    async with session.head(url, allow_redirects=True) as response:
                        redirected_url = str(response.url)
                    match = re.search(r'(\d+)', redirected_url)
                    if not match:
                        return None
                    video_id = match.group(1)
                    video_url = f'https://www.iesdouyin.com/share/video/{video_id}/'
                    async with session.get(video_url) as response:
                        if response.status != 200:
                            return None
                        response_text = await response.text()
                        data = self.router_data_pattern.findall(response_text)
                        if not data:
                            return None
                        try:
                            json_data = json.loads(data[0])
                            item = json_data.get('loaderData', {}).get('video_(id)/page', {}).get('videoInfoRes', {}).get('item_list', [{}])[0]
                            nickname = item.get('author', {}).get('nickname', '未知用户')
                            title = item.get('desc', '无标题')
                            create_time = item.get('create_time', 0)
                            timestamp = datetime.fromtimestamp(create_time).strftime('%Y-%m-%d') if create_time else '未知时间'
                            video = item.get('video', {}).get('play_addr', {}).get('uri', '')
                            if not video:
                                return None
                            if video.endswith(".mp3"):
                                final_video_url = video
                            elif video.startswith("https://"):
                                final_video_url = video.split("video_id=")[-1]
                            else:
                                final_video_url = f'https://www.douyin.com/aweme/v1/play/?video_id={video}'
                            images = []
                            for image in item.get('images', []) or []:
                                url_list = image.get('url_list', [])
                                if url_list:
                                    images.append(url_list[0])
                            is_gallery = len(images) > 0
                            return {
                                'nickname': nickname,
                                'title': title,
                                'timestamp': timestamp,
                                'raw_url': video_url,
                                'video_url': final_video_url,
                                'images': images,
                                'is_gallery': is_gallery
                            }
                        except (json.JSONDecodeError, IndexError, KeyError):
                            return None
            except Exception:
                if attempt == 2:
                    return None
                await asyncio.sleep(1 * (2 ** attempt))
        return None
