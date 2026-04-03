"""
微信代理服务配置文件
"""
import os

# 服务器配置
SERVER_HOST = '127.0.0.1'  # 监听地址
SERVER_PORT = 8888          # 监听端口
DEBUG = True

# Cookie配置
COOKIE_FILE = 'cookies/wechat_cookies.json'
COOKIE_EXPIRE_HOURS = 2  # Cookie有效期（小时）

# 请求配置
REQUEST_TIMEOUT = 10      # 请求超时时间（秒）
REQUEST_RETRY = 3        # 请求重试次数
REQUEST_DELAY = 1         # 请求延迟（秒）

# 微信UA池（模拟真实微信客户端）
USER_AGENTS = [
    'Mozilla/5.0 (Linux; Android 10; MI 9 Build/QKQ1.190825.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/78.0.3904.62 XWEB/2799 MMWEBSDK/20210101 Mobile Safari/537.36 MicroMessenger/8.0.1.1841(0x28000133) NetType/WIFI Language/zh_CN ABI/arm64',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.2(0x1800022f) NetType/WIFI Language/zh_CN',
    'Mozilla/5.0 (Linux; Android 11; Pixel 5 Build/RQ2A.210505.003; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.120 Mobile Safari/537.36 MicroMessenger/8.0.5(0x28000534) NetType/WIFI Language/zh_CN ABI/arm64-v8a',
]

# 日志配置
LOG_DIR = 'logs'
LOG_FILE = os.path.join(LOG_DIR, 'proxy.log')
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# 目标公众号
TARGET_BIZ = 'MzY5NTIxMTY0Nw=='  # 你提供的公众号biz值
TARGET_URL_TEMPLATE = 'https://mp.weixin.qq.com/mp/profile_ext?action=home&__biz={biz}&scene=124#wechat_redirect'
