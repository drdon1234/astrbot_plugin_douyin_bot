from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api.message_components import Nodes
from astrbot.core.star.filter.event_message_type import EventMessageType
from .parser import DouyinParser
import re

@register("astrbot_plugin_douyin_bot", "drdon1234", "自动识别抖音链接并转换为直链发送", "1.0")
class DouyinBotPlugin(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.is_auto_parse = config.get("is_auto_parse", True)
        self.parser = DouyinParser()

    async def terminate(self):
        pass

    @filter.event_message_type(EventMessageType.ALL)
    async def auto_parse(self, event: AstrMessageEvent):
        if not (self.is_auto_parse or bool(re.search(r'.?抖音解析', event.message_str))):
            return
        nodes = await self.parser.build_nodes(event)
        if nodes is None:
            return
        await event.send(event.plain_result("抖音bot为您服务 ٩( 'ω' )و"))
        await event.send(event.chain_result([Nodes(nodes)]))
