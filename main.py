from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
import astrbot.api.message_components as uploader
from astrbot.core.star.filter.event_message_type import EventMessageType
from .parser import DouyinParser

@register("astrbot_plugin_douyin_bot", "drdon1234", "自动解析抖音视频链接转换为直链发送", "1.0")
class DouyinBotPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.parser = DouyinParser()
    
    @filter.event_message_type(EventMessageType.ALL)
    async def auto_parse(self, event: AstrMessageEvent):
        print(event.message_str)
        direct_url = await self.parser.parse_urls(event.message_str)
        if direct_url:
            uploader.Video.fromURL(direct_url)
        
    async def terminate(self):
        pass
