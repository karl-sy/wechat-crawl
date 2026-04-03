#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import os

from cookie_manager import WeixinMpCrawler
from wechatarticles import PublicAccountsWeb
# ============ 核心类：认证与凭证管理 ============

class WechatAuthManager:
    """微信公众平台凭证管理类"""

    def __init__(self, credentials_file="weixin_credentials.py"):
        """
        初始化认证管理器

        Args:
            credentials_file: 凭证文件路径
        """
        self.credentials_file = credentials_file
        self.cookie = None
        self.token = None
        self.crawler = None

    def load_credentials(self):
        """
        从文件加载凭证

        Returns:
            bool: 凭证是否有效
        """
        try:
            if not os.path.exists(self.credentials_file):
                print(f"凭证文件 {self.credentials_file} 不存在，需要登录获取")
                return False

            # 动态导入模块
            import importlib.util
            spec = importlib.util.spec_from_file_location("credentials", self.credentials_file)
            credentials = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(credentials)

            # 获取token和cookie
            self.token = getattr(credentials, 'token', '')
            self.cookie = getattr(credentials, 'cookie', '')

            if not self.token or not self.cookie:
                print("凭证文件中没有有效的token或cookie")
                return False

            print(f"已从 {self.credentials_file} 加载token和cookie")

            # 测试凭证是否有效
            return self.test_credentials()
        except Exception as e:
            print(f"加载凭证时出错: {e}")
            return False

    def test_credentials(self):
        """
        测试凭证是否有效

        Returns:
            bool: 凭证是否有效
        """
        print("正在测试保存的凭证是否有效...")

        if not self.cookie or not self.token:
            print("凭证不完整，无法测试")
            return False

        try:
            # 创建临时的PublicAccountsWeb实例
            web = PublicAccountsWeb(cookie=self.cookie, token=self.token)

            # 尝试获取一个公众号的信息（可以是任何存在的公众号）
            test_account = "微信公众平台"  # 这是一个官方账号，理论上一直存在
            result = web.get_urls(nickname=test_account, begin=0, count=1)

            # 检查返回结果
            if result is not None:
                print("保存的凭证有效，可以继续使用")
                return True
            else:
                print("保存的凭证无效，需要重新登录")
                return False
        except Exception as e:
            print(f"测试凭证时出错: {e}")
            print("将尝试重新登录获取新的凭证")
            return False

    def login_and_get_credentials(self, headless=False):
        """
        登录并获取凭证

        Args:
            headless: 是否使用无头模式

        Returns:
            bool: 登录是否成功
        """
        print("需要登录获取新的凭证...")
        self.crawler = WeixinMpCrawler(headless=headless)

        try:
            # 登录并获取凭证
            self.crawler.login()
            print("正在获取token和cookie...")
            time.sleep(5)  # 等待页面完全加载

            # 获取凭证
            self.token = self.crawler.get_token()
            self.cookie = self.crawler.get_cookie_string()

            if not self.token or not self.cookie:
                print("无法获取必要的凭证")
                return False

            # 打印凭证信息
            print("\n获取到的凭证:")
            print(f"token: {self.token}")
            print(f"cookie: {self.cookie[:50]}..." if len(self.cookie or '') > 50 else f"cookie: {self.cookie}")

            # 保存凭证到文件
            self.save_credentials()
            return True
        finally:
            if self.crawler:
                print("关闭登录浏览器...")
                self.crawler.close()

    def save_credentials(self):
        """将凭证保存到文件"""
        if not self.token or not self.cookie or not self.crawler:
            print("无法保存凭证：凭证不完整或爬虫未初始化")
            return False

        return self.crawler.save_credentials_to_py_file(self.credentials_file)

    def ensure_valid_credentials(self, headless=False):
        """
        确保有有效的凭证，必要时进行登录

        Args:
            headless: 是否使用无头模式（True表示不显示浏览器窗口）

        Returns:
            bool: 是否有有效凭证
        """
        # 尝试加载凭证
        credentials_valid = self.load_credentials()

        # 如果没有有效的凭证，进行登录
        if not credentials_valid:
            credentials_valid = self.login_and_get_credentials(headless=headless)

        return credentials_valid
