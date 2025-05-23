# 适配 AstrBot 的插件，自动识别抖音链接并转换为直链发送

## 功能特色
- ✅ 兼容QQ、微信平台
- ✅ 兼容视频、图集解析
- ✅ 提供无水印直链下载
- ✅ 智能批量处理多链接

---

## 安装方法

### 依赖库安装（重要！）

使用前请先安装以下依赖库：
- aiohttp

在您的终端输入以下命令并回车：
```
pip install aiohttp
```

### 插件安装

1. **通过 插件市场 安装**  
- 打开 "AstrBot WebUI" -> "插件市场" -> "右上角 Search"  
- 搜索任何与本项目相关的关键词，找到插件后点击安装
- 推荐通过唯一标识符搜索：```astrbot_plugin_douyin_bot```

2. **通过 Github仓库链接 安装**  
- 打开 "AstrBot WebUI" -> "插件市场" -> "右下角 '+' 按钮"  
- 输入以下地址并点击安装：
```
https://github.com/drdon1234/astrbot_plugin_douyin_bot
```

---

## 使用方法

### 自动解析模式
- **配置方式**: 打开 "AstrBot WebUI" -> "插件管理" -> 找到本插件 -> "操作" -> "插件配置" -> 将 "is_auto_parse" 设置为 "true" (默认为true)
- **使用场景**: 需要自动解析聊天中出现的抖音链接时

### 手动解析命令
- **调用方式**: 发送"抖音解析 [链接]"
- **使用场景**: 自动解析关闭时的主动调用方式

### 批量解析功能
- 机器人将依次解析所有识别到的链接，以消息集合的形式返回所有解析结果

![image](https://github.com/user-attachments/assets/f457a749-aed2-435c-9fcd-ca656e426846)

---

## 使用建议
- 在 "AstrBot WebUI" 中打开 "回复时引用消息" 功能
- 控制批量解析时的链接数量，一次解析太多会导致消息集合发送到平台的速度极慢
- 如果您需要在任何wechat平台使用本插件，请在 "插件管理" 界面禁用 "是否将解析结果打包为消息集合"

---

## 开发中的功能
- 随机视频

---

## 已知 BUG
- 微信无法正确推送视频消息（疑似AstrBot消息处理问题）
- QQ无法以单独发送的形式推送多个图片消息（疑似Napcat消息处理问题）
  
---
## 鸣谢

视频信息抓取方法参考自：[CSDN博客文章](https://blog.csdn.net/qq_53153535/article/details/141297614)
