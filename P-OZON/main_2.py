"""
文件名: main_2.py
作者: lin
版本: 1.0.0
日期: 2025-09-17
更新: 无
描述:
    Ozon 产品抓取工具，根据用户的要求，抓取一个产品页面下的所有相似产品（跟卖的商家）
    注意 要抓取到相似产品所属的商家 的 所有产品
    从用户搜索后的产品页开始 遍历点击弹出的所有的商家列表 抓取该商家的所有产品
    支持下载图片并将其插入 Excel 表格，提供抓取进度可视化。
解释器和依赖版本:
    - Python 3.12
    - DrissionPage 4.1.1.2
    - pandas 2.3.0
    - openpyxl 3.1.5
    - Pillow 11.3.0
"""

import os
import io
import re
from time import sleep
from datetime import datetime


import pandas as pd
import requests
from tqdm import tqdm
import questionary
from PIL import Image as PILImage

from core.insert_images_to_excel import insert_images_from_column
from DrissionPage import ChromiumPage

# 全局配置
config = {
    "url": r"https://www.ozon.ru/product",  # 要抓取的网页地址
    "out_filename": "结果.xlsx",  # 输出 Excel 文件名
    "image_dir": "图片",  # 图片保存目录
    "max_workers": 1,  # 最大并发线程数，未使用多线程
    "batch_size": 20,  # 每批次写入 Excel 的数据条数
    "max_products": 100,  # 最大抓取的产品数量，用户可修改
    "scroll_pause": 1,  # 每次下滑等待加载的秒数
    "download_image": False,  # 是否下载图片
    "insert_image": False,  # 是否将图片插入表格
}


def append_to_excel(data: dict | list[dict]):
    """
    将字典或字典列表追加到 Excel 文件中。
    - data: 单个 dict 或多个 dict (list[dict])
    - filename: Excel 文件路径
    """
    filename = config["out_filename"]

    if isinstance(data, dict):
        data = [data]

    if os.path.exists(filename):
        df = pd.read_excel(filename)
    else:
        df = pd.DataFrame()

    new_df = pd.DataFrame(data)
    df = pd.concat([df, new_df], ignore_index=True)

    df.to_excel(filename, index=False)


def parse_page(page: ChromiumPage):
    """健壮版解析函数，支持局部刷新重试"""
    index = 1


if __name__ == "__main__":
    print("这是一个可视化的网页数据抓取工具，用于抓取 Ozon.ru 上的产品信息，对于你选定的商品，遍历所有跟卖商家，抓取他们的所有商品，输出到表格中")
    print("""
    将会抓取以下字段：
        product_id              商品Id
        primary_category        一级类目
        secondary_category      二级类目
        tertiary_category       三级类目
        green_price_rub         绿标价（卢布）
        green_price_cny         绿标价（￥）
        black_price_cny         黑标价（￥）
        lowest_follow_price_cny 跟卖最低价（￥）
        sales_volume            销量
        follow_seller_count     跟卖数量
        product_rating          商品评分
        product_link            商品链接
        country_of_origin       商品生产国家
        product_info            商品信息
        first_crawled_at        商品数据首次获取时间
        last_updated_at         商品数据更新时间

    """)

    main_page = ChromiumPage()
    main_page.get(config["url"])
    print("网页打开成功")

    if os.path.exists(config["out_filename"]):
        now = datetime.now()
        config["out_filename"] = now.strftime("结果_%Y%m%d_%H%M%S.xlsx")

    input("请在网页中进行搜索/筛选/登录操作后，按回车开始抓取数据...")

    all_tabs = main_page.browser.get_tabs()
    if not all_tabs:
        print("没有找到可用标签页！")
        exit(1)

    main_page = all_tabs[0]

    print(f"Page Title: {main_page.title}")
    print("正在抓取数据，请勿操作页面！")

    div_webBestSeller = main_page.ele('@data-widget=webBestSeller', timeout=5)
    if div_webBestSeller:
        button_webBestSeller = div_webBestSeller.ele('tag:button')

        if button_webBestSeller:
            button_webBestSeller.click()

            div_sellerList = main_page.ele('#seller-list', timeout=5)

            if div_sellerList:
                button_more_sellerList = div_sellerList.ele('tag:button', timeout=5)

                if button_more_sellerList:
                    button_more_sellerList.click()






















