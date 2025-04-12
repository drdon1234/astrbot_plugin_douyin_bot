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

    async def terminate(self):
        pass
    
    @filter.event_message_type(EventMessageType.ALL)
    async def auto_parse(self, event: AstrMessageEvent):
        results = await self.parser.parse_urls(event.message_str)
        if len(results) == 0:
            return
        nodes = [
            uploader.Plain(f"抖音bot为您服务 ٩( 'ω' )و")
        ]
        sender_name = "抖音bot"
        sender_id = int(event.get_self_id()) or 10000
        for result in results:
            if result and not isinstance(result, Exception):
                nodes.append(
                    uploader.Node(
                        name = sender_name,
                        uin = sender_id,
                        content = [
                            uploader.Plain(f"视频链接：{result['raw_url']}\n标题：{result['title']}\n作者：{result['nickname']}\n发布时间：{result['timestamp']}")
                        ]
                    )
                )
                nodes.append(
                    uploader.Node(
                        name = sender_name,
                        uin = sender_id,
                        content = [
                            uploader.Video.fromURL(result['video_url'])
                        ]
                    )
                )
        yield event.chain_result([nodes])
