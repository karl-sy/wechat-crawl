#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import random
import pickle
import csv
import os
from datetime import datetime, timedelta
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

from wechatarticles import PublicAccountsWeb


# ============ 通用辅助函数 ============

def create_accounts_excel_file(filename="accounts.xlsx", example_accounts=None):
    """创建示例公众号名称Excel文件"""
    if example_accounts is None:
        example_accounts = ["同济计算机", "腾讯科技", "人民日报", "新华社", "CSDN"]

    # 如果文件已存在，不覆盖
    if os.path.exists(filename):
        print(f"文件 {filename} 已存在。")
        return

    # 创建DataFrame并写入Excel
    df = pd.DataFrame({"nickname": example_accounts})
    df.to_excel(filename, index=False)

    print(f"已创建示例公众号名称文件: {filename}")
    print(f"包含的公众号: {', '.join(example_accounts)}")


def read_accounts_from_excel(filename="accounts.xlsx"):
    """从Excel文件读取公众号名称列表"""
    if not os.path.exists(filename):
        print(f"文件 {filename} 不存在，将创建示例文件。")
        create_accounts_excel_file(filename)

    accounts = []
    try:
        # 读取Excel文件
        df = pd.read_excel(filename)

        # 检查是否有nickname列
        if 'nickname' in df.columns:
            # 过滤掉空值并转换为列表
            accounts = df['nickname'].dropna().astype(str).tolist()
        else:
            print(f"警告: Excel文件 {filename} 中没有找到'nickname'列")
    except Exception as e:
        print(f"读取 {filename} 时出错: {e}")

    print(f"从 {filename} 读取到 {len(accounts)} 个公众号")
    return accounts


def get_existing_article_titles(date=None):
    """获取指定日期Excel文件中的文章标题"""
    if date is None:
        # 使用昨天的日期
        date = datetime.now().date() - timedelta(days=1)

    # 根据日期生成文件名
    file_name = f"{date.month}月{date.day}号wechat_articles.xlsx"

    # 检查文件是否存在
    if not os.path.exists(file_name):
        print(f"昨天的文件 {file_name} 不存在，不需要检查重复文章")
        return set()

    try:
        # 读取Excel文件
        df = pd.read_excel(file_name, sheet_name='文章信息', skiprows=3)

        # 检查是否有title列
        if 'title' in df.columns:
            # 提取文章标题并转换为集合
            titles = set(df['title'].dropna().tolist())
            print(f"从昨天的文件 {file_name} 中读取到 {len(titles)} 个文章标题")
            return titles
        else:
            print(f"警告: Excel文件 {file_name} 中没有找到'title'列")
            return set()
    except Exception as e:
        print(f"读取昨天的文件 {file_name} 时出错: {e}")
        return set()


def save_articles_to_excel(articles_info, stats=None, output_file=None, filter_existing=True, stats_message=None):
    """将爬取的文章信息保存到Excel文件，可选择是否排除已存在的文章"""
    # 如果未指定输出文件名，则根据当前日期生成
    if output_file is None:
        current_date = datetime.now()
        output_file = f"{current_date.month}月{current_date.day}号wechat_articles.xlsx"

    filtered_articles = articles_info
    filtered_count = 0

    # 只有当需要过滤已存在文章时才执行
    if filter_existing:
        # 获取昨天Excel文件中的文章标题
        existing_titles = get_existing_article_titles()

        # 过滤掉已存在的文章
        filtered_articles = []

        for article in articles_info:
            if article['title'] in existing_titles:
                filtered_count += 1
                print(f"文章已存在于昨天的Excel中，将被过滤: {article['title']}")
            else:
                filtered_articles.append(article)

        print(f"过滤掉 {filtered_count} 篇已存在的文章，剩余 {len(filtered_articles)} 篇新文章")

    # 如果没有文章信息
    if not filtered_articles:
        print("没有文章信息可以保存")

        # 如果有统计信息，则创建一个Excel文件保存
        if stats:
            # 创建自定义统计信息
            if stats_message is None:
                stats_message = f"需要爬取的公众号一共{stats.get('total_accounts', 0)}个，" \
                                f"其中{stats.get('accounts_updated_recently', 0)}个最近有更新，" \
                                f"其中{stats.get('accounts_not_updated', 0)}个最近未更新，" \
                                f"过滤掉{filtered_count}篇已存在的文章"

            df_stats = pd.DataFrame([{'统计信息': stats_message}])
            df_stats.to_excel(output_file, index=False)
            print(f"\n统计信息已保存到 {output_file}")
        return

    # 创建文章信息DataFrame
    df_articles = pd.DataFrame(filtered_articles)

    # 调整列的顺序，确保nickname, title, link, publish_time在前面
    preferred_columns = ['nickname', 'title', 'link', 'publish_time', 'publish_date']
    available_columns = [col for col in preferred_columns if col in df_articles.columns]
    other_columns = [col for col in df_articles.columns if col not in preferred_columns]
    all_columns = available_columns + other_columns
    df_articles = df_articles[all_columns]

    # 创建ExcelWriter对象
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # 如果有统计信息，先写入统计信息
        if stats:
            # 创建自定义统计信息
            if stats_message is None:
                stats_message = f"需要爬取的公众号一共{stats.get('total_accounts', 0)}个，" \
                                f"其中{stats.get('accounts_updated_recently', 0)}个最近有更新，" \
                                f"其中{stats.get('accounts_not_updated', 0)}个最近未更新，" \
                                f"过滤掉{filtered_count}篇已存在的文章"

            stats_row = pd.DataFrame([{'统计信息': stats_message}])
            stats_row.to_excel(writer, sheet_name='文章信息', index=False)

            # 写入文章信息，从第4行开始（给统计信息留出空间）
            df_articles.to_excel(writer, sheet_name='文章信息', startrow=3, index=False)
        else:
            # 没有统计信息，直接写入文章信息
            df_articles.to_excel(writer, sheet_name='文章信息', index=False)

    print(f"\n文章信息已保存到 {output_file}")
    if stats and stats_message:
        print(f"统计信息: {stats_message}")
    print(f"共保存了 {len(filtered_articles)} 篇文章")






# ============ 核心类：文章内容分析 ============

class ArticleAnalyzer:
    """文章内容分析类"""

    def __init__(self):
        """初始化分析器"""
        pass

    def fetch_article_content(self, url):
        """
        从文章链接获取完整内容

        Args:
            url: 文章URL

        Returns:
            str: 文章内容文本
        """
        try:
            # 设置请求头，模拟浏览器访问
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Connection': 'keep-alive'
            }

            # 随机延迟，避免请求过于频繁
            time.sleep(random.uniform(1, 3))

            # 请求文章页面获取内容
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                # 使用BeautifulSoup解析HTML
                soup = BeautifulSoup(response.text, 'html.parser')

                # 提取文章内容 - 微信文章通常在rich_media_content中
                content_element = soup.select_one('#js_content') or soup.select_one('.rich_media_content')
                if content_element:
                    # 获取所有文本，清理空白字符
                    content_text = content_element.get_text(strip=True)
                    return content_text

                # 如果找不到特定元素，尝试获取整个页面文本
                return soup.get_text(strip=True)

            # 如果请求失败
            print(f"请求文章内容失败，状态码: {response.status_code}")
            return ""

        except Exception as e:
            print(f"获取文章内容时出错: {e}")
            return ""

    def calculate_keyword_score(self, text, keywords, weights):
        """
        计算文本中关键词得分

        Args:
            text: 文本内容
            keywords: 关键词列表
            weights: 权重列表，与关键词一一对应

        Returns:
            tuple: (关键词计数字典, 总分数)
        """
        # 确保关键词和权重长度一致
        if len(keywords) != len(weights):
            print("关键词和权重数量不匹配")
            return {}, 0

        # 统计每个关键词出现次数
        keyword_counts = {}
        total_score = 0

        for i, keyword in enumerate(keywords):
            # 统计关键词出现次数 (不区分大小写)
            count = text.lower().count(keyword.lower())
            keyword_counts[keyword] = count

            # 计算加权分数
            score = count * weights[i]
            total_score += score

        return keyword_counts, total_score

    def analyze_articles_with_keywords(self, articles, keywords, weights):
        """
        分析文章列表中的关键词

        Args:
            articles: 文章信息列表
            keywords: 关键词列表
            weights: 权重列表

        Returns:
            list: 分析后的文章列表 (添加了keyword_counts和keyword_score字段)
        """
        # 限制关键词数量
        if len(keywords) > 3:
            print("关键词数量超过限制，只使用前3个关键词")
            keywords = keywords[:3]
            weights = weights[:3]

        # 如果权重列表不够长，用1补齐
        while len(weights) < len(keywords):
            weights.append(1)

        print(f"开始分析 {len(articles)} 篇文章中的关键词: {keywords}")
        print(f"关键词权重: {weights}")

        # 为每篇文章获取内容并计算关键词分数
        for i, article in enumerate(articles):
            print(f"[{i + 1}/{len(articles)}] 处理文章: {article['title']}")

            # 获取文章内容
            content = self.fetch_article_content(article['link'])
            article['content_length'] = len(content)

            # 计算关键词分数
            keyword_counts, total_score = self.calculate_keyword_score(content, keywords, weights)

            # 保存到文章信息
            article['keyword_counts'] = str(keyword_counts)  # 转为字符串以便保存到Excel
            article['keyword_score'] = total_score

            # 打印分数
            print(f"- 关键词统计: {keyword_counts}")
            print(f"- 总分数: {total_score}")

            # 添加随机延迟，避免请求过于频繁
            if i < len(articles) - 1:  # 如果不是最后一篇文章
                delay = random.uniform(2, 5)
                print(f"等待 {delay:.2f} 秒后处理下一篇文章...")
                time.sleep(delay)

        # 根据关键词得分排序文章
        sorted_articles = sorted(articles, key=lambda x: x.get('keyword_score', 0), reverse=True)

        print(f"===== 完成关键词分析，按分数排序 =====")
        for i, article in enumerate(sorted_articles[:10]):  # 打印前10篇
            if i < len(sorted_articles):
                print(f"{i + 1}. {article['title']} - 分数: {article.get('keyword_score', 0)}")

        return sorted_articles


# ============ 高级封装类：微信文章管理器 ============

class WechatArticleManager:
    """微信公众号文章管理器 - 高级封装类"""

    def __init__(self, credentials_file="weixin_credentials.py", headless=False):
        """
        初始化管理器

        Args:
            credentials_file: 凭证文件路径
            headless: 是否使用无头模式（True表示不显示浏览器窗口）
        """
        self.auth_manager = WechatAuthManager(credentials_file)
        self.crawler = None
        self.analyzer = ArticleAnalyzer()
        self.headless = headless  # 保存无头模式设置

    def ensure_authentication(self):
        """
        确保身份验证有效

        Returns:
            bool: 身份验证是否成功
        """
        if self.auth_manager.ensure_valid_credentials(headless=self.headless):
            # 创建或更新爬虫实例
            if not self.crawler:
                self.crawler = ArticleCrawler(self.auth_manager.cookie, self.auth_manager.token)
            else:
                self.crawler.set_credentials(self.auth_manager.cookie, self.auth_manager.token)
            return True
        else:
            print("无法获取有效凭证，操作中止")
            return False

    def crawl_multiple_accounts(self, nickname_list, articles_per_account=10, days=2, output_file=None):
        """
        爬取多个公众号的最近文章

        Args:
            nickname_list: 公众号名称列表
            articles_per_account: 每个公众号获取的文章数量
            days: 获取最近几天的文章
            output_file: 输出文件名，默认为None(自动生成)

        Returns:
            tuple: (成功标志, 文章列表)
        """
        # 确保认证有效
        if not self.ensure_authentication():
            return False, []

        # 爬取文章
        articles, stats = self.crawler.fetch_wechat_articles(
            nickname_list,
            articles_per_account=articles_per_account,
            days=days
        )

        if not articles:
            print("未获取到任何文章")
            return False, []

        # 保存到Excel
        if output_file is None:
            current_date = datetime.now()
            output_file = f"{current_date.month}月{current_date.day}号wechat_articles.xlsx"

        save_articles_to_excel(articles, stats, output_file)

        print(f"\n爬取完成！共爬取了 {len(articles)} 篇最近 {days} 天发布的文章")
        print(f"数据已保存到 {output_file}")

        return True, articles

    def crawl_account_history(self, nickname, max_articles=100, output_file=None):
        """
        爬取单个公众号的历史文章

        Args:
            nickname: 公众号名称
            max_articles: 最大爬取文章数量
            output_file: 输出文件名，默认为None(自动生成)

        Returns:
            tuple: (成功标志, 文章列表)
        """
        # 确保认证有效
        if not self.ensure_authentication():
            return False, []

        # 爬取文章
        articles = self.crawler.fetch_account_history(nickname, max_articles)

        if not articles:
            print(f"未获取到公众号 '{nickname}' 的任何文章")
            return False, []

        # 如果未指定输出文件名，则使用公众号名称自动生成
        if output_file is None:
            current_date = datetime.now()
            output_file = f"{nickname}_{current_date.strftime('%Y%m%d')}_历史文章.xlsx"

        # 创建简单的统计信息
        stats_message = f"公众号 '{nickname}' 历史文章爬取结果，共获取 {len(articles)} 篇文章"

        # 保存到Excel（不过滤已存在的文章）
        save_articles_to_excel(
            articles_info=articles,
            output_file=output_file,
            filter_existing=False,
            stats_message=stats_message
        )

        print(f"\n爬取完成！共爬取了公众号 '{nickname}' 的 {len(articles)} 篇历史文章")
        print(f"数据已保存到 {output_file}")

        return True, articles

    def search_keywords_in_account(self, nickname, keywords, weights=None, max_articles=20, output_file=None):
        """
        搜索关键词并排序公众号文章

        Args:
            nickname: 公众号名称
            keywords: 关键词列表
            weights: 权重列表，默认都为1
            max_articles: 最大爬取文章数量
            output_file: 输出文件名，默认为None(自动生成)

        Returns:
            tuple: (成功标志, 排序后的文章列表)
        """
        # 默认权重
        if weights is None:
            weights = [1] * len(keywords)

        # 确保认证有效
        if not self.ensure_authentication():
            return False, []

        # 爬取文章
        articles = self.crawler.fetch_account_history(nickname, max_articles)

        if not articles:
            print(f"未获取到公众号 '{nickname}' 的任何文章")
            return False, []

        # 分析关键词并排序
        sorted_articles = self.analyzer.analyze_articles_with_keywords(articles, keywords, weights)

        # 如果未指定输出文件名，则使用关键词和公众号名称自动生成
        if output_file is None:
            keyword_str = "_".join(keywords)
            current_date = datetime.now()
            output_file = f"{nickname}_{keyword_str}_{current_date.strftime('%Y%m%d')}.xlsx"

        # 创建简单的统计信息
        keywords_str = ", ".join([f"{keywords[i]}(权重{weights[i]})" for i in range(len(keywords))])
        stats_message = f"公众号 '{nickname}' 关键词搜索: {keywords_str}，共分析 {len(sorted_articles)} 篇文章"

        # 保存到Excel（不过滤已存在的文章）
        save_articles_to_excel(
            articles_info=sorted_articles,
            output_file=output_file,
            filter_existing=False,
            stats_message=stats_message
        )

        print(f"\n搜索完成！共处理公众号 '{nickname}' 的 {len(sorted_articles)} 篇文章")
        print(f"数据已按关键词分数从高到低排序并保存到 {output_file}")

        return True, sorted_articles