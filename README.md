# 适配 AstrBot 的随机小姐姐美图短视频插件

## 安装方法

1. **通过 插件市场 安装**  
- 打开 "AstrBot WebUI" -> "插件市场" -> "右上角 Search"  
- 搜索任何与本项目相关的关键词，找到插件后点击安装
- 推荐通过唯一标识符搜索：```astrbot_plugin_showme_xjj```

2. **通过 Github仓库链接 安装**  
- 打开 "AstrBot WebUI" -> "插件市场" -> "右下角 '+' 按钮"  
- 输入以下地址并点击安装：
```
https://github.com/drdon1234/astrbot_plugin_showme_xjj
```

---

## 使用说明

### 指令帮助

- **随机短视频**  
```xjj视频```

- **随机美图**  
```xjj图片```

- **获取指令帮助**  
```xjj```

- **热重载config配置**  
```重载xjj配置```

---

## 配置文件修改（重要！）

使用前请先修改配置文件 `config.yaml`：

### 平台设置
```
platform:
  type: "napcat" # 消息平台，兼容 napcat, llonebot, lagrange
  http_host: "127.0.0.1" # HTTP 服务器 IP，非 docker 部署一般为 127.0.0.1，docker 部署一般为宿主机局域网 IP
  http_port: 2333 # HTTP 服务器端口，通常为 2333 或 3000
  api_token: "" # HTTP 服务器 token，没有则不填
```

### 接口设置
```
api:
  # video_api: 视频接口
  # picture_api: 图片接口
    # url: 接口url
    # pipeline: 解析流程
      # fetch: 需要解析网站响应
      # direct_url: 媒体文件直链，QQ手机端可以免下载浏览
      # download_url: 需要先下载到本地的媒体文件链接
      # 任何解析流程必须以 direct_url 或 download_url 结尾
      # 除以上关键字外的流程如 data 或 raw_url 代表网站返回的json具体元素，支持迭代解析响应
    
  video_api:
    # 小姐姐质量和画质都不错，建议
    - url: "https://v2.api-m.com/api/meinv?return=302"
      pipeline: "direct_url"

    # 小姐姐质量和画质都不错，建议
    - url: "http://api.yujn.cn/api/zzxjj.php?type=video"
      pipeline: "direct_url"
      
    # 视频版每日摸鱼，不适合作为随机视频
    # - url: "https://dayu.qqsuu.cn/moyuribaoshipin/apis.php?type=json"
    #   pipeline: "fetch | data | direct_url"

    # 小姐姐质量和画质都比较一般且需要下载，不建议
    # - url: "https://onexiaolaji.cn/RandomPicture/api/api-video.php"
    #   pipeline: "fetch | raw_url | download_url"

    # 小姐姐质量和画质都比较一般，不建议
    # - url: "https://tucdn.wpon.cn/api-girl/index.php"
    #   pipeline: "direct_url"

  picture_api:
    # 暂时只找到一个图片接口
    - url: "https://api.zhcnli.cn/api/sjtp/tupian.php?type=hs"
      pipeline: "direct_url"
```

### 缓存设置
```
download:
  cache_folder: "/app/sharedFolder" # 媒体文件需要下载时使用的保存路径
```

---

## 依赖库安装（重要！）

使用前请先安装以下依赖库：
- aiohttp
- PyYAML

在您的终端输入以下命令并回车：
```
pip install <module>
```
*使用具体模块名替换 &lt;module&gt;*

---

## Docker 部署注意事项

如果您是 Docker 部署，请务必为消息平台容器挂载视频缓存文件所在的文件夹，否则消息平台将无法解析文件路径。

示例挂载方式(NapCat)：
- 对 AstrBot：`/vol3/1000/dockerSharedFolder -> /app/sharedFolder`
- 对 NapCat：`/vol3/1000/dockerSharedFolder -> /app/sharedFolder`

---

## 已知 BUG

---

## 开发中的功能

---
