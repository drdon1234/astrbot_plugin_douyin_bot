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
        self.default_timeout = aiohttp.ClientTimeout(total=10)  # 10秒超时

    def extract_router_data(self, text):
        start_flag = 'window._ROUTER_DATA = '
        start_idx = text.find(start_flag)
        if start_idx == -1:
            return None
        brace_start = text.find('{', start_idx)
        if brace_start == -1:
            return None
        i = brace_start
        stack = []
        while i < len(text):
            if text[i] == '{':
                stack.append('{')
            elif text[i] == '}':
                stack.pop()
                if not stack:
                    return text[brace_start:i+1]
            i += 1
        return None

    async def fetch_video_info(self, session, video_id):
        url = f'https://www.iesdouyin.com/share/video/{video_id}/'
        try:
            async with session.get(url, headers=self.headers, timeout=10) as response:
                response_text = await response.text()
                json_str = self.extract_router_data(response_text)
                if not json_str:
                    print('未找到 _ROUTER_DATA')
                    return None
                json_str = json_str.replace('\\u002F', '/').replace('\\/', '/')
                try:
                    json_data = json.loads(json_str)
                except Exception as e:
                    print('JSON解析失败', e)
                    return None
                loader_data = json_data.get('loaderData', {})
                video_info = None
                for v in loader_data.values():
                    if isinstance(v, dict) and 'videoInfoRes' in v:
                        video_info = v['videoInfoRes']
                        break
                if not video_info or 'item_list' not in video_info or not video_info['item_list']:
                    print('未找到视频信息')
                    return None
                item_list = video_info['item_list'][0]
                title = item_list['desc']
                nickname = item_list['author']['nickname']
                timestamp = datetime.fromtimestamp(item_list['create_time']).strftime('%Y-%m-%d')
                thumb_url = item_list['video']['cover']['url_list'][0]
                video = item_list['video']['play_addr']['uri']
                if video.endswith('.mp3'):
                    video_url = video
                elif video.startswith('https://'):
                    video_url = video
                else:
                    video_url = f'https://www.douyin.com/aweme/v1/play/?video_id={video}'
                images = [img['url_list'][0] for img in (item_list.get('images') or []) if 'url_list' in img]
                is_gallery = len(images) > 0
                return {
                    'title': title,
                    'nickname': nickname,
                    'timestamp': timestamp,
                    'thumb_url': thumb_url,
                    'video_url': video_url,
                    'images': images,
                    'is_gallery': is_gallery
                }
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            print(f'请求错误：{e}')
            return None
        except Exception as e:
            print(f'未知错误：{e}')
            return None

    async def get_redirected_url(self, session, url):
        try:
            async with session.head(url, allow_redirects=True, timeout=10) as response:
                return str(response.url)
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            print(f'重定向请求错误：{e}')
            return url
        except Exception as e:
            print(f'重定向未知错误：{e}')
            return url

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
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                print(f'解析请求错误：{e}')
                return None
            except Exception as e:
                print(f'解析未知错误：{e}')
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
            async with aiohttp.ClientSession(timeout=self.default_timeout) as session:
                tasks = [self.parse(session, url) for url in urls]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, Exception):
                        print(f"解析时发生异常：{result}")
                        continue
                    if result:
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
