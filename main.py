from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api.message_components import Plain, Video, Node, Nodes
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
        try:
            results = await self.parser.parse_urls(event.message_str)
            if len(results) == 0:
                return
            nodes = []
            sender_name = "抖音bot"
            sender_id = int(event.get_self_id()) or 10000
            for result in results:
                if result and not isinstance(result, Exception):
                    nodes.append(
                        Node(
                            name=sender_name,
                            uin=sender_id,
                            content=[
                                Plain(f"标题：{result['title']}\n作者：{result['nickname']}\n发布时间：{result['timestamp']}")
                            ]
                        )
                    )
                    nodes.append(
                        Node(
                            name=sender_name,
                            uin=sender_id,
                            content=[
                                Video.fromURL(result['video_url'])
                            ]
                        )
                    )
            await event.send(event.plain_result("抖音bot为您服务 ٩( 'ω' )و"))
            await event.send(event.chain_result([Nodes(nodes)]))
        except Exception as e:
            print(f"处理消息时发生错误：{e}")
