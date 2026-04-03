import sys
from collections import defaultdict
from datetime import datetime
from typing import List

# ------- 引入原框架中的核心类与工具函数 -------
try:
    from wechat_utils import (
        # read_accounts_from_excel,
        save_articles_to_excel,   # 直接复用原有 Excel 输出逻辑
    )
    from article_manager import ArticleAnalyzer
    from wechat_manager import WechatArticleManager
except ImportError as e:
    print("❌ 无法导入 wechat_mp_crawler 中的核心组件，请确认文件名/包路径！")
    print("   原始错误信息：", e)
    sys.exit(1)

def crawl_and_rank(
    account_list: List[str] = None,
    articles_per_account: int = 15,
    days: int = 4,
    keywords: List[str] = None,
    weights: List[float] = None,
    headless: bool = False
):
    """
    主流程：读取账号列表 → 爬取最近文章 → 关键词分析排序 → 写入 Excel。
    """
    # -------- 读取公众号列表 --------
    if not account_list:
        print(f"⚠️  无任何公众号名称，程序终止。")
        return

    print(f"✅ 将爬取的公众号：{', '.join(account_list)}")
    print(f"   每个账号最多抓取 {articles_per_account} 篇，范围：最近 {days} 天。")

    # -------- 初始化管理器并完成认证 --------
    manager = WechatArticleManager(headless=headless)
    if not manager.ensure_authentication():
        # ensure_authentication() 里会自行打印错误原因
        return

    # -------- 抓取所有公众号的最近文章（保持原逻辑不变） --------
    articles, stats = manager.crawler.fetch_wechat_articles(
        nickname_list=account_list,
        articles_per_account=articles_per_account,
        days=days
    )

    if not articles:
        print("⚠️  未抓取到任何文章，程序结束。")
        return

    # -------- 关键词设置（若用户未指定则交互式输入 / 用默认） --------
    if not keywords:
        # 默认使用与示例相同的关键词
        keywords = ["人工智能", "数据科学", "程序设计"]
    if not weights or len(weights) != len(keywords):
        # 权重不足则全部设为 1
        weights = [1] * len(keywords)

    print(f"\n🔍 关键词列表：{keywords}")
    print(f"   权重列表： {weights}")

    analyzer = ArticleAnalyzer()

    # -------- 按公众号分组并做关键词排序 --------
    articles_by_account = defaultdict(list)
    for art in articles:
        articles_by_account[art["nickname"]].append(art)

    sorted_articles_all = []
    for nickname in account_list:
        acc_articles = articles_by_account.get(nickname, [])
        if not acc_articles:
            print(f"🚫  公众号「{nickname}」在最近 {days} 天内无文章，跳过关键词分析。")
            continue

        print(f"\n=== 开始分析公众号「{nickname}」的 {len(acc_articles)} 篇文章 ===")
        ranked = analyzer.analyze_articles_with_keywords(
            acc_articles,
            keywords=keywords,
            weights=weights
        )
        sorted_articles_all.extend(ranked)

    # -------- 输出到 Excel（复用原 save_articles_to_excel） --------
    current_date = datetime.now()
    output_file = f"{current_date.month}_{current_date.day}_wechat_articles.xlsx"

    print(f"\n💾 正在写入 Excel：{output_file}")
    save_articles_to_excel(
        articles_info=sorted_articles_all,
        stats=stats,
        output_file=output_file,
        filter_existing=True   # 仍然按照昨天的文件去重
    )

    print("\n🎉 全部完成！")
    print(f"   Excel 已生成：{output_file}")


# ------------------ 程序入口 ------------------
if __name__ == "__main__":
    # 你可以根据需要改成 argparse / configparser，这里保持示例的直接调用风格
    crawl_and_rank(
        account_list = ["探索AGI", "大海 程序员转AI日记"],
        articles_per_account=20,
        days=3,
        headless=False                              # ✅ 设为 True 则无头运行
    )
