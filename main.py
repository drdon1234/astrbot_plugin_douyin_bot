from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api.message_components import Plain, Video, Node, Nodes
from astrbot.core.star.filter.event_message_type import EventMessageType
from .parser import DouyinParser

@register("astrbot_plugin_douyin_bot", "drdon1234", "自动识别抖音链接并转换为视频直链", "1.0")
class DouyinBotPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.parser = DouyinParser()

    async def terminate(self):
        pass
    
    @filter.event_message_type(EventMessageType.ALL)
    async def auto_parse(self, event: AstrMessageEvent):
        nodes = await self.parser.build_nodes(event)
        if nodes is None:
            return
        yield event.plain_result("抖音bot为您服务 ٩( 'ω' )و")
        await event.send(event.chain_result([Nodes(nodes)]))
