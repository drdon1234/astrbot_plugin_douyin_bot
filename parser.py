import aiohttp
import asyncio
import re
import json
from datetime import datetime
from astrbot.api.message_components import Plain, Video, Image, Node, Nodes

class DouyinParser:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 8.0.0; SM-G955U Build/R16NW) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36',
            'Referer': 'https://www.douyin.com/?is_from_mobile_home=1&recommend=1'
        }
        self.semaphore = asyncio.Semaphore(10)

    async def build_nodes(self, event, is_auto_pack):
        try:
            input_text = event.message_str
            urls = self.extract_video_links(input_text)
            if not urls:
                return None
            nodes = []
            sender_name = "抖音bot"
            platform = event.get_platform_name()
            sender_id = event.get_self_id()
            if platform != "webchat" and platform != "gewechat":
                try:
                    sender_id = int(sender_id)
                except:
                    sender_id = 10000
            async with aiohttp.ClientSession() as session:
                tasks = [self.parse(session, url) for url in urls]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    if result and not isinstance(result, Exception):
                        if is_auto_pack:
                            text_node = Node(
                                name=sender_name,
                                uin=sender_id,
                                content=[
                                    Plain(f"标题：{result['title']}\n作者：{result['nickname']}\n发布时间：{result['timestamp']}")
                                ]
                            )
                        else:
                            text_node = Plain(f"标题：{result['title']}\n作者：{result['nickname']}\n发布时间：{result['timestamp']}")
                        nodes.append(text_node)
                        if result['is_gallery']:
                            if is_auto_pack:
                                gallery_node_content = []
                                for image_url in result['images']:
                                    image_node = Node(
                                        name=sender_name,
                                        uin=sender_id,
                                        content=[
                                            Image.fromURL(image_url)
                                        ]
                                    )
                                    gallery_node_content.append(image_node)
                                parent_gallery_node = Node(
                                    name=sender_name,
                                    uin=sender_id,
                                    content=gallery_node_content
                                )
                                nodes.append(parent_gallery_node)
                            else:
                                for image_url in result['images']:
                                    nodes.append(
                                        Image.fromURL(image_url)
                                    )
                        else:
                            if is_auto_pack:
                                video_node = Node(
                                    name=sender_name,
                                    uin=sender_id,
                                    content=[
                                        Video.fromURL(result['video_url'])
                                    ]
                                )
                            else:
                                video_node = Video.fromURL(result['video_url'], cover=result['thumb_url'])
                            nodes.append(video_node)
            if not nodes:
                return None
            return nodes
        except Exception as e:
            print(f"构建节点时发生错误：{e}", flush=True)
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def extract_video_links(input_text):
        result_links = []
        mobile_pattern = r'https?://v\.douyin\.com/[^\s]+'
        mobile_links = re.findall(mobile_pattern, input_text)
        result_links.extend(mobile_links)
        web_pattern = r'https?://(?:www\.)?douyin\.com/[^\s]*?(\d{19})[^\s]*'
        web_matches = re.finditer(web_pattern, input_text)
        for match in web_matches:
            video_id = match.group(1)
            standardized_url = f"https://www.douyin.com/video/{video_id}"
            result_links.append(standardized_url)
        return result_links

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
                    title = item_list['desc']
                    nickname = item_list['author']['nickname']
                    timestamp = datetime.fromtimestamp(item_list['create_time']).strftime('%Y-%m-%d')
                    video = item_list['video']['play_addr']['uri']
                    thumb_url = item_list['video']['cover']['url_list'][0]
                    video_url = (
                        video if video.endswith(".mp3") else
                        video.split("video_id=")[-1] if video.startswith("https://") else
                        f'https://www.douyin.com/aweme/v1/play/?video_id={video}'
                    )
                    images = [image['url_list'][0] for image in (item_list.get('images') or []) if 'url_list' in image]
                    is_gallery = len(images) > 0
                    return {
                        # 'raw_url': url,
                        'title': title,
                        'nickname': nickname,
                        'timestamp': timestamp,
                        'thumb_url': thumb_url,
                        'video_url': video_url,
                        'images': images,
                        'is_gallery': is_gallery
                    }
                else:
                    return None
        except aiohttp.ClientError as e:
            print(f'请求错误：{e}')
            return None
