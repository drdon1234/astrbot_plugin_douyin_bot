from astrbot.api.event import AstrMessageEvent
import aiohttp
import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

logger = logging.getLogger(__name__)


class MessageAdapter:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.platform_type = self.config["platform"]["type"]
        self.http_host = self.config["platform"]["http_host"]
        self.http_port = self.config["platform"]["http_port"]
        self.api_token = self.config["platform"]["api_token"]

    def get_headers(self) -> Dict[str, str]:
        headers = {'Content-Type': 'application/json'}
        if self.api_token:
            headers['Authorization'] = f'Bearer {self.api_token}'
        return headers

    async def get_group_root_files(self, group_id: str) -> Dict[str, Any]:
        url = f"http://{self.http_host}:{self.http_port}/get_group_root_files"
        payload = {"group_id": group_id}
        headers = self.get_headers()

        logger.debug(f"发送给消息平台-> {payload}")

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"获取群文件根目录失败，状态码: {response.status}, 错误信息: {error_text}")

                res = await response.json()
                if res["status"] != "ok":
                    raise Exception(f"获取群文件根目录失败，状态码: {res['status']}\n完整消息: {str(res)}")

                return res["data"]

    async def create_group_file_folder(self, group_id: str, folder_name: str) -> Optional[str]:
        url = f"http://{self.http_host}:{self.http_port}/create_group_file_folder"

        if self.platform_type == 'napcat':
            payload = {
                "group_id": group_id,
                "folder_name": folder_name
            }
        elif self.platform_type == 'llonebot':
            payload = {
                "group_id": group_id,
                "name": folder_name
            }
        elif self.platform_type == 'lagrange':
            payload = {
                "group_id": group_id,
                "name": folder_name,
                "parent_id": "/"
            }
        else:
            raise Exception("消息平台配置有误, 只能是'napcat', 'llonebot'或'lagrange'")

        headers = self.get_headers()
        logger.debug(f"发送给消息平台-> {payload}")

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"创建群文件夹失败，状态码: {response.status}, 错误信息: {error_text}")

                res = await response.json()
                logger.debug(f"消息平台返回-> {res}")

                if res["status"] != "ok":
                    raise Exception(f"创建群文件夹失败，状态码: {res['status']}\n完整消息: {str(res)}")

                try:
                    return res["data"]["folder_id"]
                except Exception:
                    return None

    async def get_group_folder_id(self, group_id: str, folder_name: str = '/') -> str:
        if folder_name == '/':
            return '/'

        data = await self.get_group_root_files(group_id)
        for folder in data.get('folders', []):
            if folder.get('folder_name') == folder_name:
                return folder.get('folder_id')

        folder_id = await self.create_group_file_folder(group_id, folder_name)
        if folder_id is None:
            data = await self.get_group_root_files(group_id)
            for folder in data.get('folders', []):
                if folder.get('folder_name') == folder_name:
                    return folder.get('folder_id')
            return "/"

        return folder_id

    async def upload_file(self, event: AstrMessageEvent, path: str, name: str = None, type = "video", folder_name: str = '/') -> Dict[
        str, Any]:
        is_url = path.startswith(('http://', 'https://'))
        
        if is_url:
            file_path = path
    
            if name is None:
                from urllib.parse import urlparse
                url_path = urlparse(path).path
                file_name = url_path.split('/')[-1] or "downloaded_file"
            else:
                file_name = name
        else:
            file_path = Path(path)
            if not file_path.exists():
                raise FileNotFoundError(f"文件不存在: {path}")
            
            if name is None:
                file_name = file_path.name
            else:
                file_name = f"{name}{file_path.suffix}"
    
        is_private = event.is_private_chat()
        target_id = event.get_sender_id() if is_private else event.get_group_id()
        url_type = "send_private_msg" if is_private else "send_group_msg"
        url = f"http://{self.http_host}:{self.http_port}/{url_type}"
        
        payload = {
            "user_id" if is_private else "group_id": target_id,
            "message": [
                {
                    "type": type,
                    "data": {
                        "file": str(file_path)
                    }
                }
            ]
        }
        
        try:
            headers = self.get_headers()
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    response.raise_for_status()
                    res = await response.json()
                    
                    if res["status"] != "ok":
                        logger.warning(f"文件上传失败: {res.get('message')}")
                        raise Exception(f"API返回错误: {res.get('message')}")
                    
                    return {
                        "total": 1,
                        "success_count": 1,
                        "failed_count": 0,
                        "details": {
                            "successes": [res.get("data")],
                            "errors": []
                        }
                    }
        except Exception as e:
            logger.warning(f"文件上传失败: {e}")
            raise
