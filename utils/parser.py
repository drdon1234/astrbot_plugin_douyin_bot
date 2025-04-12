import os
import aiohttp
import json
from urllib.parse import urlparse, parse_qs
import uuid
import mimetypes
from typing import Dict, Any, Tuple, Optional


async def get_url(api_config: Dict[str, Any], cache_folder: str) -> str:
    url = api_config["url"]
    pipeline_steps = api_config["pipeline"].split(" | ")

    if pipeline_steps == ["direct_url"]:
        return url
    elif pipeline_steps == ["download_url"]:
        return await download_file(url, cache_folder)

    return await process_pipeline(url, pipeline_steps, cache_folder)


async def download_file(url: str, cache_folder: str) -> str:
    os.makedirs(cache_folder, exist_ok=True)
    base_filename = str(uuid.uuid4())

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        async with session.get(url, allow_redirects=True) as response:
            if response.status != 200:
                raise Exception(f"下载失败: {url}, 状态码: {response.status}")

            extension = None

            if "content-disposition" in response.headers:
                content_disp = response.headers["content-disposition"]
                if "filename=" in content_disp:
                    filename_part = content_disp.split("filename=")[1].strip('"\'')
                    if "." in filename_part:
                        extension = os.path.splitext(filename_part)[1]

            if not extension:
                parsed_url = urlparse(url)
                query_params = parse_qs(parsed_url.query)
                if "fileName" in query_params and query_params["fileName"]:
                    filename_param = query_params["fileName"][0]
                    if "." in filename_param:
                        extension = os.path.splitext(filename_param)[1]

            if not extension:
                content_type = response.headers.get("Content-Type", "")
                if content_type:
                    guessed_ext = mimetypes.guess_extension(content_type.split(';')[0].strip())
                    if guessed_ext:
                        extension = guessed_ext

            if not extension:
                path_extension = os.path.splitext(parsed_url.path)[1]
                if path_extension:
                    extension = path_extension

            if not extension:
                if "video" in url.lower() or "mp4" in url.lower():
                    extension = ".mp4"
                else:
                    extension = ".jpg"

            filename = f"{base_filename}{extension}"
            filepath = os.path.join(cache_folder, filename)

            content = await response.read()

            with open(filepath, 'wb') as file:
                file.write(content)

            return filepath


async def process_pipeline(url: str, steps: list, cache_folder: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as session:
        current_data = None
        current_url = url
        response_url = None

        for step in steps:
            if step == "fetch":
                current_url, current_data, response_url = await fetch_data(session, current_url)
            elif step == "direct_url":
                return current_url
            elif step == "download_url":
                return await download_file_with_session(session, current_url, cache_folder)
            else:
                if current_data is None:
                    raise Exception(f"没有数据可以提取'{step}'")

                current_url, current_data = extract_field(current_data, step, current_url)

    raise Exception("流程未以direct_url或download_url结束")


async def download_file_with_session(session, url: str, cache_folder: str) -> str:
    os.makedirs(cache_folder, exist_ok=True)
    base_filename = str(uuid.uuid4())

    async with session.get(url, allow_redirects=True) as response:
        if response.status != 200:
            raise Exception(f"下载失败: {url}, 状态码: {response.status}")

        extension = None

        if "content-disposition" in response.headers:
            content_disp = response.headers["content-disposition"]
            if "filename=" in content_disp:
                filename_part = content_disp.split("filename=")[1].strip('"\'')
                if "." in filename_part:
                    extension = os.path.splitext(filename_part)[1]

        if not extension:
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            if "fileName" in query_params and query_params["fileName"]:
                filename_param = query_params["fileName"][0]
                if "." in filename_param:
                    extension = os.path.splitext(filename_param)[1]

        if not extension:
            content_type = response.headers.get("Content-Type", "")
            if content_type:
                guessed_ext = mimetypes.guess_extension(content_type.split(';')[0].strip())
                if guessed_ext:
                    extension = guessed_ext

        if not extension:
            path_extension = os.path.splitext(parsed_url.path)[1]
            if path_extension:
                extension = path_extension

        if not extension:
            if "video" in url.lower() or "mp4" in url.lower():
                extension = ".mp4"
            else:
                extension = ".jpg"

        filename = f"{base_filename}{extension}"
        filepath = os.path.join(cache_folder, filename)

        content = await response.read()

        with open(filepath, 'wb') as file:
            file.write(content)

        return filepath


async def fetch_data(session, url: str) -> Tuple[str, Optional[Dict], Optional[str]]:
    async with session.get(url, allow_redirects=True) as response:
        if response.status != 200:
            raise Exception(f"获取URL失败: {url}, 状态码: {response.status}")

        response_url = str(response.url)

        try:
            text = await response.text()
            data = json.loads(text)
            return url, data, response_url
        except json.JSONDecodeError:
            return response_url, None, response_url


def extract_field(data: Dict[str, Any], field: str, current_url: str) -> Tuple[str, Any]:
    if not isinstance(data, dict):
        raise Exception(f"无法从非字典数据中提取字段")

    if field in data:
        value = data[field]

        if isinstance(value, str) and (value.startswith("http://") or value.startswith("https://")):
            return value, None
        else:
            return current_url, value
    else:
        raise Exception(f"在响应中找不到键'{field}'")
