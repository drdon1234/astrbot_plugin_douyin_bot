import aiohttp
import asyncio
import re
import json
from datetime import datetime

class DouyinParser:
    semaphore = asyncio.Semaphore(10)  # 类变量，所有实例共享

    def __init__(self, session):
        self.session = session
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 8.0.0; SM-G955U Build/R16NW) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36',
            'Referer': 'https://www.douyin.com/?is_from_mobile_home=1&recommend=1'
        }

    async def get_redirected_url(self, url):
        async with self.session.head(url, allow_redirects=True) as response:
            return str(response.url)

    async def fetch_video_info(self, video_id):
        url = f'https://www.iesdouyin.com/share/video/{video_id}/'
        try:
            async with self.session.get(url, headers=self.headers) as response:
                response_text = await response.text()
                data = re.findall(r'_ROUTER_DATA\s*=\s*(\{.*?\});', response_text)
                if data:
                    json_data = json.loads(data[0])
                    item_list = json_data['loaderData']['video_(id)/page']['videoInfoRes']['item_list'][0]
                    nickname = item_list['author']['nickname']
                    title = item_list['desc']
                    timestamp = datetime.fromtimestamp(item_list['create_time']).strftime('%Y-%m-%d')
                    video = item_list['video']['play_addr']['uri']
                    video_url = f'https://www.douyin.com/aweme/v1/play/?video_id={video}' if 'mp3' not in video else video
                    return {
                        'nickname': nickname,
                        'title': title,
                        'timestamp': timestamp,
                        'video_url': video_url,
                    }
                else:
                    return None
        except aiohttp.ClientError as e:
            print(f'请求错误：{e}')
            return None

    async def parse(self, url):
        async with self.semaphore:  # 使用类变量信号量
            redirected_url = await self.get_redirected_url(url)
            match = re.search(r'(\d+)', redirected_url)
            if match:
                video_id = match.group(1)
                return await self.fetch_video_info(video_id)
            else:
                return None

    @staticmethod
    def extract_video_links(input_text):
        douyin_video_pattern = r'https?://(?:www\.|v\.)?douyin\.com/(?:video/\d+|[^\s]+)'
        video_links = re.findall(douyin_video_pattern, input_text)
        return video_links

    async def parse_urls(self, urls):
        tasks = [self.parse(url) for url in urls]
        results = await asyncio.gather(*tasks)
        return results

async def main():
    input_text = """
    9.71 a@a.nQ 02/11 Slp:/ # 肯恰那 https://v.douyin.com/5JJ_ZvXkGz0/ 复制此链接，打开Dou音搜索，直接观看视频！
    https://www.douyin.com/video/7488299765604666682 https://v.douyin.com/t_ToZGLYIBk
    """

    urls = DouyinParser.extract_video_links(input_text)

    async with aiohttp.ClientSession() as session:
        parser = DouyinParser(session)
        results = await parser.parse_urls(urls)

        for url, result in zip(urls, results):
            if result:
                print(f"URL: {url}")
                print(f"作者：{result['nickname']}")
                print(f"标题：{result['title']}")
                print(f"发布时间：{result['timestamp']}")
                print(f"视频直链：{result['video_url']}\n\n")
            else:
                print(f"解析失败！URL: {url}")

if __name__ == "__main__":
    asyncio.run(main())
