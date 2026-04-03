
import time
import random
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import re

from wechatarticles import PublicAccountsWeb



# ============ 核心类：文章爬取管理 ============

class ArticleCrawler:
    """微信公众号文章爬取管理类"""

    def __init__(self, cookie=None, token=None):
        """
        初始化文章爬取器

        Args:
            cookie: cookie字符串
            token: token字符串
        """
        self.cookie = cookie
        self.token = token
        self.web = None

        # 如果有cookie和token，就初始化web实例
        if self.cookie and self.token:
            self.init_web()

    def init_web(self):
        """初始化Web连接实例"""
        if self.cookie and self.token:
            self.web = PublicAccountsWeb(cookie=self.cookie, token=self.token)
            return True
        else:
            print("缺少必要的cookie或token，无法初始化连接")
            return False

    def set_credentials(self, cookie, token):
        """
        设置凭证

        Args:
            cookie: cookie字符串
            token: token字符串
        """
        self.cookie = cookie
        self.token = token
        return self.init_web()

    def extract_publish_time_from_url(self, url):
        """
        从微信公众号文章URL中提取发布时间

        Args:
            url: 文章URL

        Returns:
            tuple: (发布日期对象, 发布日期字符串)
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

                # 方法1：从JavaScript中提取时间戳 - 这是正确的方法
                page_text = response.text

                # 查找JavaScript中的时间戳模式
                # 根据搜索结果，微信文章中时间戳的模式类似：var ct = "1567005049"
                timestamp_patterns = [
                    r'var\s+ct\s*=\s*["\'](\d{10})["\']',  # var ct = "1567005049"
                    r'ct\s*=\s*["\'](\d{10})["\']',  # ct = "1567005049"
                    r'"ct"\s*:\s*["\']?(\d{10})["\']?',  # "ct": "1567005049" 或 "ct": 1567005049
                    r'create_time["\']?\s*:\s*["\']?(\d{10})["\']?',  # create_time: 1567005049
                    r'publish_time["\']?\s*:\s*["\']?(\d{10})["\']?',  # publish_time: 1567005049
                    # 新增更多可能的模式
                    r'var\s+t\s*=\s*["\'](\d{10})["\']',  # var t = "1567005049"
                    r'"(\d{10})",n="(\d{10})",s="([^"]+)"',  # 匹配类似 "1575860164",n="1575539255",s="2019-12-05" 的模式
                    r't\s*=\s*["\'](\d{10})["\']',  # t = "1567005049"
                    r'["\'](\d{10})["\'],\s*n\s*=\s*["\'](\d{10})["\']',  # 时间戳对的模式
                ]

                # 尝试从JavaScript中提取时间戳
                for pattern in timestamp_patterns:
                    matches = re.findall(pattern, page_text, re.IGNORECASE)
                    if matches:
                        try:
                            # 处理不同的匹配结果格式
                            timestamp = None

                            if isinstance(matches[0], tuple):
                                # 如果匹配结果是元组（多个捕获组），取第一个作为时间戳
                                for item in matches[0]:
                                    if item.isdigit() and len(item) == 10:
                                        timestamp = int(item)
                                        break
                            else:
                                # 如果匹配结果是字符串
                                if matches[0].isdigit() and len(matches[0]) == 10:
                                    timestamp = int(matches[0])

                            if timestamp:
                                # 验证时间戳是否合理（2000年到2030年之间）
                                if 946684800 <= timestamp <= 1893456000:  # 2000-01-01 到 2030-01-01
                                    # 将时间戳转换为日期对象
                                    publish_date_obj = datetime.fromtimestamp(timestamp)
                                    publish_date = publish_date_obj.date()
                                    publish_date_str = publish_date_obj.strftime('%Y-%m-%d %H:%M:%S')

                                    print(f"从JavaScript中提取到时间戳: {timestamp}, 转换后的时间: {publish_date_str}")
                                    return publish_date, publish_date_str
                                else:
                                    print(f"时间戳 {timestamp} 不在合理范围内，跳过")

                        except (ValueError, OverflowError) as e:
                            print(f"时间戳转换错误: {e}")
                            continue

                # 方法2：查找更复杂的JavaScript时间设置模式
                # 寻找类似 document.getElementById("publish_time") 的JavaScript代码块
                js_patterns = [
                    r'document\.getElementById\("publish_time"\)[^}]+?s\s*=\s*["\']([^"\']+)["\']',
                    r'getElementById\("publish_time"\)[^}]+?(\d{4}-\d{2}-\d{2})',
                ]

                for pattern in js_patterns:
                    matches = re.findall(pattern, page_text, re.IGNORECASE | re.DOTALL)
                    if matches:
                        for match in matches:
                            # 尝试解析找到的日期字符串
                            date_formats = ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S']
                            for date_format in date_formats:
                                try:
                                    publish_date_obj = datetime.strptime(match, date_format)
                                    publish_date = publish_date_obj.date()
                                    print(f"从JavaScript日期字符串中提取到时间: {match}")
                                    return publish_date, match
                                except ValueError:
                                    continue

                # 方法3：尝试查找微信文章页面中的发布时间元素（备用方法）
                publish_time_element = soup.select_one('#publish_time') or soup.select_one('.publish_time')
                if publish_time_element:
                    publish_time_text = publish_time_element.text.strip()
                    if publish_time_text:  # 如果元素有内容
                        # 尝试解析日期
                        date_formats = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y年%m月%d日 %H:%M', '%Y年%m月%d日']
                        for date_format in date_formats:
                            try:
                                publish_date = datetime.strptime(publish_time_text, date_format).date()
                                return publish_date, publish_time_text
                            except ValueError:
                                continue

                # 方法4：在页面源码中查找其他时间模式（最后备用）
                date_patterns = [
                    r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}',
                    r'\d{4}-\d{2}-\d{2}',
                    r'\d{4}年\d{1,2}月\d{1,2}日 \d{1,2}:\d{1,2}',
                    r'\d{4}年\d{1,2}月\d{1,2}日'
                ]

                # 遍历页面查找可能的日期
                for pattern in date_patterns:
                    matches = re.findall(pattern, page_text)
                    if matches:
                        # 尝试解析找到的第一个日期
                        for match in matches:
                            date_formats = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y年%m月%d日 %H:%M', '%Y年%m月%d日']
                            for date_format in date_formats:
                                try:
                                    publish_date = datetime.strptime(match, date_format)
                                    return publish_date.date(), match
                                except ValueError:
                                    continue

            # 如果从页面内容无法获取到时间，返回None
            print(f"无法从URL {url} 提取发布时间")
            return None, ""

        except Exception as e:
            print(f"提取文章发布时间时出错: {e}")
            return None, ""

    def fetch_articles_from_account(self, nickname, count=10, filter_recent_days=None, max_attempts=10,
                                    time_filter_func=None, stop_on_outdated=False):
        """
        从单个公众号获取文章

        Args:
            nickname: 公众号名称
            count: 获取的文章数量
            filter_recent_days: 如果不为None，只获取最近几天的文章
            max_attempts: 最大尝试次数
            time_filter_func: 时间过滤函数，接收article_date参数，返回布尔值
            stop_on_outdated: 是否在发现第一篇过期文章时就停止，适用于批量爬取多个公众号时

        Returns:
            list: 文章信息列表 [{nickname, title, link, publish_time}, ...]
        """
        if not self.web:
            print("Web连接未初始化，请先设置有效凭证")
            return []

        articles_info = []

        # 设置日期范围（如果需要）
        today = datetime.now().date()
        date_range = None
        if filter_recent_days:
            date_range = [today - timedelta(days=i) for i in range(filter_recent_days)]
            print(f"将只保留最近 {filter_recent_days} 天的文章")

        # 使用随机延迟，避免操作过于规律被检测
        delay = random.uniform(3, 8)
        print(f"等待 {delay:.2f} 秒后开始获取文章...")
        time.sleep(delay)

        attempt = 0
        offset = 0
        collected = 0
        has_more = True
        outdated_found = False  # 标记是否找到过期文章

        # 最大批次，每批次获取数量
        batch_size = 5  # 减小批次大小，减少漏爬风险

        # 记录连续空结果次数
        empty_results_count = 0

        # 记录已获取的文章链接，避免重复
        fetched_links = set()

        while has_more and collected < count and attempt < max_attempts and not outdated_found:
            try:
                print(f"获取公众号 '{nickname}' 的文章，批次 {attempt + 1}，偏移量 {offset}...")

                # 获取文章数据
                articles = self.web.get_urls(nickname=nickname, begin=offset, count=batch_size)

                if not articles:
                    empty_results_count += 1
                    print(f"未获取到文章，连续空结果次数: {empty_results_count}")

                    # 只有连续3次获取不到文章，才认为确实没有更多文章了
                    if empty_results_count >= 3:
                        print(f"连续{empty_results_count}次未获取到文章，可能已到达文章列表末尾")
                        has_more = False
                        break
                    else:
                        # 尽管没有获取到文章，仍然尝试增加偏移量继续获取
                        # 使用较小的增量，避免跳过文章
                        print("尝试增加偏移量继续获取...")
                        offset += 1  # 只增加1而不是batch_size，更小的增量减少漏爬
                        attempt += 1

                        # 添加额外延迟，可能是因为请求过于频繁导致的限制
                        extra_delay = random.uniform(8, 15)
                        print(f"添加额外延迟 {extra_delay:.2f} 秒...")
                        time.sleep(extra_delay)
                        continue
                else:
                    # 重置连续空结果计数
                    empty_results_count = 0

                print(f"获取到 {len(articles)} 篇文章，正在处理...")

                # 标记是否在此批次中添加了任何文章
                added_in_batch = False

                # 处理获取到的文章
                for article in articles:
                    # 从文章数据中提取所需信息
                    title = article.get('title', '无标题')
                    link = article.get('link', '无链接')

                    # 检查是否已经处理过这个链接
                    if link in fetched_links:
                        print(f"文章 '{title}' 已经爬取过，跳过")
                        continue

                    # 从URL中提取发布时间
                    article_date = None
                    publish_date_str = ''

                    if link != '无链接':
                        article_date, publish_date_str = self.extract_publish_time_from_url(link)

                        if article_date:
                            # 如果有自定义的时间过滤函数
                            if time_filter_func and not time_filter_func(article_date):
                                print(f"文章 '{title}' 不符合时间过滤条件，跳过")

                                # 如果设置了stop_on_outdated，并且文章确实是因为太旧而被过滤
                                # 这里我们假设time_filter_func是用来检查文章是否在最近的日期范围内
                                if stop_on_outdated:
                                    print(f"发现不符合时间条件的文章，停止爬取公众号 '{nickname}'")
                                    outdated_found = True
                                    break

                                continue

                            # 如果需要过滤最近几天的文章
                            if date_range and article_date not in date_range:
                                print(f"文章 '{title}' 发布于 {article_date}，不在指定的日期范围内")

                                # 无论是否已收集文章，只要文章日期早于范围，如果启用了stop_on_outdated，就停止
                                if stop_on_outdated:
                                    print(f"发现超出日期范围的文章，停止爬取公众号 '{nickname}'")
                                    outdated_found = True
                                    break

                                # 原有的逻辑：只有已经收集了文章才因为日期早于范围而停止
                                if article_date < min(date_range) and collected > 0:
                                    print("已找到早于指定日期范围的文章，停止获取")
                                    has_more = False
                                    break
                                continue

                            # 添加文章信息
                            articles_info.append({
                                'nickname': nickname,
                                'title': title,
                                'link': link,
                                'publish_time': publish_date_str,
                                'publish_date': article_date.strftime('%Y-%m-%d')
                            })

                            # 记录已获取的链接
                            fetched_links.add(link)

                            collected += 1
                            added_in_batch = True
                            print(f"[{collected}/{count}] 已添加文章: {title}")

                            # 如果已经收集足够的文章，则终止循环
                            if collected >= count:
                                print(f"已达到目标数量 {count} 篇文章，停止获取")
                                has_more = False
                                break
                        else:
                            print(f"从URL无法提取到发布时间: {link}")

                # 如果发现了过期文章，退出主循环
                if outdated_found:
                    print(f"由于发现过期文章，提前停止爬取公众号 '{nickname}'")
                    break

                # 更新偏移量，准备获取下一批文章
                if added_in_batch:
                    # 如果这批次成功添加了文章，使用常规偏移量增量
                    offset += batch_size // 2  # 使用一半的批次大小作为增量，提高重叠度
                else:
                    # 如果这批次没有添加任何文章，使用较小的增量尝试
                    offset += 1  # 增加最小偏移量，尝试捕获可能漏掉的文章

                # 如果还有更多文章需要获取，添加随机延迟
                if has_more and collected < count:
                    delay = random.uniform(5, 10)
                    print(f"等待 {delay:.2f} 秒后获取下一批文章...")
                    time.sleep(delay)

                attempt += 1

            except Exception as e:
                attempt += 1
                print(f"获取公众号 '{nickname}' 的文章时出错 (尝试 {attempt}/{max_attempts}): {e}")
                if attempt < max_attempts:
                    delay = random.uniform(10, 15)
                    print(f"等待 {delay:.2f} 秒后重试...")
                    time.sleep(delay)
                else:
                    print(f"已达到最大尝试次数 {max_attempts}，停止获取")
                    break

        if outdated_found:
            print(f"提前终止：公众号 '{nickname}' 的文章已超出时间范围，共获取到 {len(articles_info)} 篇符合条件的文章")
        else:
            print(f"共获取到公众号 '{nickname}' 的 {len(articles_info)} 篇文章")

        return articles_info

    def fetch_wechat_articles(self, nickname_list, articles_per_account=10, days=2):
        """
        爬取多个公众号的文章

        Args:
            nickname_list: 公众号名称列表
            articles_per_account: 每个公众号获取的文章数量(最大值)
            days: 获取最近几天的文章 (默认为2，即今天和昨天)

        Returns:
            tuple: (文章信息列表 [{nickname, title, link, publish_time}, ...], 统计信息)
        """
        if not self.web:
            print("Web连接未初始化，请先设置有效凭证")
            return [], {}

        # 获取当前日期和昨天日期
        today = datetime.now().date()
        date_range = [today - timedelta(days=i) for i in range(days)]

        print(f"当前日期: {today}，将抓取最近 {days} 天发布的文章")

        # 存储所有文章信息的列表
        all_articles_info = []

        # 统计信息
        total_accounts = len(nickname_list)
        accounts_updated_recently = 0
        accounts_not_updated = 0

        # 定义时间过滤函数：只保留最近days天的文章
        def recent_days_filter(article_date):
            return article_date in date_range

        for i, nickname in enumerate(nickname_list):
            print(f"\n正在获取公众号 '{nickname}' 的文章 ({i + 1}/{total_accounts})...")

            # 获取该公众号的文章（使用时间过滤）
            # 启用stop_on_outdated，一旦发现过期文章就停止爬取当前公众号
            account_articles = self.fetch_articles_from_account(
                nickname=nickname,
                count=articles_per_account,
                time_filter_func=recent_days_filter,
                stop_on_outdated=True  # 添加这个参数，一旦发现过期文章就停止
            )

            # 添加文章到总列表
            all_articles_info.extend(account_articles)

            # 更新统计信息
            if account_articles:
                accounts_updated_recently += 1
                print(f"公众号 '{nickname}' 最近 {days} 天有更新，找到 {len(account_articles)} 篇文章")
            else:
                accounts_not_updated += 1
                print(f"公众号 '{nickname}' 最近 {days} 天无更新")

            # 在每个公众号处理后添加额外的随机延迟
            if i < len(nickname_list) - 1:  # 如果不是最后一个公众号
                extra_delay = random.uniform(8, 15)
                print(f"处理下一个公众号前等待 {extra_delay:.2f} 秒...")
                time.sleep(extra_delay)

        # 准备统计信息
        stats = {
            'total_accounts': total_accounts,
            'accounts_updated_recently': accounts_updated_recently,
            'accounts_not_updated': accounts_not_updated,
            'date': today.strftime('%Y-%m-%d')
        }

        return all_articles_info, stats

    def fetch_account_history(self, nickname, max_articles=100):
        """
        爬取单个公众号的历史文章（最多max_articles篇）

        Args:
            nickname: 公众号名称
            max_articles: 最大爬取文章数量，默认100

        Returns:
            list: 文章信息列表 [{nickname, title, link, publish_time, publish_date}, ...]
        """
        if not self.web:
            print("Web连接未初始化，请先设置有效凭证")
            return []

        print(f"===== 开始爬取公众号 '{nickname}' 的历史文章 =====")

        # 获取该公众号的文章（不使用时间过滤）
        articles = self.fetch_articles_from_account(
            nickname=nickname,
            count=max_articles
        )

        print(f"===== 完成爬取公众号 '{nickname}' 的历史文章，共获取 {len(articles)} 篇 =====")
        return articles


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
