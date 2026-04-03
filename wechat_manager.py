from auth_manager import WechatAuthManager
from article_manager import ArticleCrawler,ArticleAnalyzer
from wechat_utils import *

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