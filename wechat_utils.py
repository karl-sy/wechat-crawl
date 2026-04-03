#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from datetime import datetime, timedelta
import pandas as pd


# ============ 通用辅助函数 ============

# def create_accounts_excel_file(filename="accounts.xlsx", example_accounts=None):
#     """创建示例公众号名称Excel文件"""
#     if example_accounts is None:
#         example_accounts = ["同济计算机", "腾讯科技", "人民日报", "新华社", "CSDN"]
#
#     # 如果文件已存在，不覆盖
#     if os.path.exists(filename):
#         print(f"文件 {filename} 已存在。")
#         return
#
#     # 创建DataFrame并写入Excel
#     df = pd.DataFrame({"nickname": example_accounts})
#     df.to_excel(filename, index=False)
#
#     print(f"已创建示例公众号名称文件: {filename}")
#     print(f"包含的公众号: {', '.join(example_accounts)}")
#
#
# def read_accounts_from_excel(filename="accounts.xlsx"):
#     """从Excel文件读取公众号名称列表"""
#     if not os.path.exists(filename):
#         print(f"文件 {filename} 不存在，将创建示例文件。")
#         create_accounts_excel_file(filename)
#
#     accounts = []
#     try:
#         # 读取Excel文件
#         df = pd.read_excel(filename)
#
#         # 检查是否有nickname列
#         if 'nickname' in df.columns:
#             # 过滤掉空值并转换为列表
#             accounts = df['nickname'].dropna().astype(str).tolist()
#         else:
#             print(f"警告: Excel文件 {filename} 中没有找到'nickname'列")
#     except Exception as e:
#         print(f"读取 {filename} 时出错: {e}")
#
#     print(f"从 {filename} 读取到 {len(accounts)} 个公众号")
#     return accounts


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
