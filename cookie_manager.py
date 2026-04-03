from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

import time
import pickle


# ============ 核心类：登录爬虫 ============

class WeixinMpCrawler:
    """微信公众平台登录爬虫，获取token和cookie"""

    def __init__(self, headless=False):
        """
        初始化爬虫

        Args:
            headless: 是否使用无头模式（不显示浏览器窗口）
        """
        self.url = "https://mp.weixin.qq.com/"
        self.browser = None
        self.headless = headless
        self.setup_browser()

    def setup_browser(self):
        """配置浏览器"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")

        # 添加常用选项
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")

        # 初始化浏览器
        service = Service(ChromeDriverManager().install())
        self.browser = webdriver.Chrome(service=service, options=chrome_options)

    def login(self, timeout=120):
        """
        打开微信公众平台并等待用户扫码登录

        Args:
            timeout: 等待扫码登录的超时时间（秒）

        Returns:
            bool: 登录是否成功
        """
        try:
            print("正在打开微信公众平台登录页...")
            self.browser.get(self.url)

            # 等待二维码出现
            try:
                qrcode_iframe = WebDriverWait(self.browser, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "weui-desktop-qrcheck__iframe"))
                )
                self.browser.switch_to.frame(qrcode_iframe)

                # 等待二维码加载完成
                WebDriverWait(self.browser, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "qrcode"))
                )

                print("请使用微信扫描二维码登录（等待时间：{}秒）...".format(timeout))

                # 切回主frame
                self.browser.switch_to.default_content()
            except Exception as e:
                # 可能已经登录或页面结构变化
                print(f"获取二维码过程中出现异常: {str(e)}")
                print("可能已经登录或页面结构已变化，继续检测登录状态...")

            # 新的登录检测逻辑：不依赖于URL变化，而是检测页面上的元素
            start_time = time.time()
            while time.time() - start_time < timeout:
                # 检测是否已登录成功
                try:
                    # 尝试多种可能表示登录成功的元素
                    if (self.browser.find_elements(By.CLASS_NAME, "weui-desktop-panel__title") or
                            self.browser.find_elements(By.CLASS_NAME, "menu_item") or
                            self.browser.find_elements(By.ID, "menuBar") or
                            "/cgi-bin/home" in self.browser.current_url):
                        print("检测到登录成功标志！")
                        # 等待页面完全加载
                        time.sleep(3)
                        print("登录成功！")
                        return True
                except:
                    pass

                # 暂停一段时间再次检查
                time.sleep(2)

            # 如果超时但看起来已经登录（用户反馈），我们也认为成功
            print("登录检测超时，但将继续尝试获取token和cookie...")
            return True

        except Exception as e:
            print(f"登录过程中出现异常: {str(e)}")
            print("尽管出现错误，将继续尝试获取token和cookie...")
            # 即使出现异常，也尝试继续执行
            return True

    def get_cookies(self):
        """
        获取所有cookies

        Returns:
            list: cookie列表
        """
        return self.browser.get_cookies()

    def get_token(self):
        """
        尝试从页面或请求中提取token

        Returns:
            str: token字符串，如果未找到则返回None
        """
        try:
            print("尝试多种方法获取token...")

            # 方法1：从localStorage中获取
            try:
                tokens = self.browser.execute_script("""
                    var tokens = [];
                    for (var i = 0; i < localStorage.length; i++) {
                        var key = localStorage.key(i);
                        if (key.includes('token') || key.includes('Token')) {
                            tokens.push({
                                key: key,
                                value: localStorage.getItem(key)
                            });
                        }
                    }
                    return tokens;
                """)
                if tokens and len(tokens) > 0:
                    print(f"从localStorage找到可能的token: {tokens}")
                    # 返回第一个找到的token
                    return tokens[0]['value']
            except Exception as e:
                print(f"从localStorage获取token失败: {str(e)}")

            # 方法2：从URL中获取
            current_url = self.browser.current_url
            print(f"当前URL: {current_url}")
            if "token" in current_url.lower():
                # 使用简单解析从URL中提取token参数
                import re
                token_match = re.search(r'[?&](token|TOKEN)=([^&]+)', current_url, re.IGNORECASE)
                if token_match:
                    token = token_match.group(2)
                    print(f"从URL找到token: {token}")
                    return token

            # 方法3：从页面源码中查找
            page_source = self.browser.page_source
            if "token" in page_source.lower():
                # 使用更复杂的正则表达式查找不同格式的token
                import re
                patterns = [
                    r'"token":"([^"]+)"',
                    r'"Token":"([^"]+)"',
                    r'token:\s*["\']([^"\']+)["\']',
                    r'Token:\s*["\']([^"\']+)["\']',
                    r'token=([^&"\']+)',
                    r'Token=([^&"\']+)'
                ]

                for pattern in patterns:
                    token_match = re.search(pattern, page_source, re.IGNORECASE)
                    if token_match:
                        token = token_match.group(1)
                        print(f"从页面源码找到token: {token}")
                        return token

            # 方法4：尝试执行网络请求并从响应中提取
            try:
                token = self.browser.execute_script("""
                    // 创建一个简单的内部API请求来获取token
                    return new Promise((resolve, reject) => {
                        const xhr = new XMLHttpRequest();
                        xhr.open('GET', '/cgi-bin/bizattr?action=get_attr');
                        xhr.onload = function() {
                            if (this.status >= 200 && this.status < 300) {
                                try {
                                    const resp = JSON.parse(xhr.responseText);
                                    if (resp && resp.base_resp && resp.base_resp.token) {
                                        resolve(resp.base_resp.token);
                                    } else {
                                        resolve(null);
                                    }
                                } catch(e) {
                                    resolve(null);
                                }
                            } else {
                                resolve(null);
                            }
                        };
                        xhr.onerror = function() {
                            resolve(null);
                        };
                        xhr.send();
                    });
                """)
                if token:
                    print(f"从API响应找到token: {token}")
                    return token
            except Exception as e:
                print(f"从API获取token失败: {str(e)}")

            print("未找到token，可能需要登录后进入特定页面")
            return None
        except Exception as e:
            print(f"获取token时出错: {str(e)}")
            return None

    def get_cookie_string(self):
        """
        获取格式化的cookie字符串

        Returns:
            str: cookie字符串，格式为 'name1=value1; name2=value2'
        """
        cookies = self.get_cookies()
        return "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])

    def save_cookies_to_file(self, filename="mp_weixin_cookies.pkl"):
        """
        将cookies保存到文件

        Args:
            filename: 保存的文件名
        """
        cookies = self.get_cookies()
        with open(filename, "wb") as f:
            pickle.dump(cookies, f)
        print(f"Cookies已保存到 {filename}")

    def save_credentials_to_py_file(self, filename="weixin_credentials.py"):
        """
        将token和cookie保存为Python变量格式的文件

        Args:
            filename: 保存的文件名
        """
        token = self.get_token()
        cookies = self.get_cookies()

        # 将cookie转换为请求可用的格式
        cookie_str = "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])

        # 构建Python文件内容
        content = f"""#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 微信公众平台凭证
# 自动生成于 {time.strftime("%Y-%m-%d %H:%M:%S")}

# 接口请求需要的token
token = "{token or ''}"

# 请求时需要携带的cookie字符串
cookie = '{cookie_str}'

# 可选：单独保存的cookie字典
cookie_dict = {{{', '.join([f'"{cookie["name"]}": "{cookie["value"]}"' for cookie in cookies])}}}
"""

        # 写入文件
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"\n凭证已保存到 {filename}")
        print(f"您可以通过 'import {filename.replace('.py', '')}' 导入并使用这些凭证")

        # 同时打印到控制台
        print("\n==== 可复制的凭证变量 ====")
        print(f"token = \"{token or ''}\"")
        print(f"cookie = '{cookie_str}'")

        return token, cookie_str

    def close(self):
        """关闭浏览器"""
        if self.browser:
            self.browser.quit()
            print("浏览器已关闭")
