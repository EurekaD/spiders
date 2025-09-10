"""
文件名: main.py
作者: lin
版本: 1.0.0
日期: 2025-09-10
更新: 无
描述:
    Shein 产品抓取工具，用于批量抓取 Shein.com 上产品的 SKU、标题、价格、首图和详情页链接，
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
    "url": r"https://us.shein.com/",  # 要抓取的网页地址
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


def extract_sku_from_href(href_str: str) -> str | None:
    """从 href 中提取 SKU"""
    try:
        m = re.search(r"/product/([^/]+)/?", href_str)
        if not m:
            return None
        slug = m.group(1)
        sku_str = slug.split("-")[-1]
        return sku_str
    except Exception as e:
        print(e)
        return None


def safe_download(url: str, save_dir: str, sku: str, retries: int = 3, timeout: int = 10) -> str | None:
    """
    安全下载图片函数，带重试。
    - url: 图片 URL
    - save_dir: 保存路径（不含文件名）
    - retries: 最大重试次数
    - timeout: 网络请求超时时间
    返回 True 表示下载成功，False 表示失败
    """
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, timeout=timeout)
            resp.raise_for_status()

            data = resp.content
            image = PILImage.open(io.BytesIO(data))

            file_name = f"{sku}.png"
            save_path = os.path.join(save_dir, file_name)

            image.save(save_path, format="PNG")
            return save_path
        except Exception as e:
            print(f"下载失败 {url}，尝试 {attempt}/{retries}，原因: {e}")
            sleep(1)
    return None


def download_images_from_excel(
        image_column: str = "img_url",
        sku_column: str = "sku",
        save_dir: str = config["image_dir"],
        out_excel_path: str | None = None
):
    """
    遍历 Excel 图片列，下载图片到指定目录，并用 sku 命名。
    - image_column: 表格中图片链接列名
    - sku_column: 表格中 SKU 列名
    - save_dir: 图片保存目录
    - out_excel_path: 输出 Excel 文件路径，如果 None 则覆盖原文件
    """
    df = pd.read_excel(config["out_filename"])

    # 确保保存目录存在
    os.makedirs(save_dir, exist_ok=True)

    pbar_image_download = tqdm(total=len(df), desc="图片下载进度")
    success_count = 0
    fail_count = 0

    # 遍历表格
    for idx, row in df.iterrows():
        url = row.get(image_column)
        sku = row.get(sku_column)
        if not url or not sku:
            pbar_image_download.update(1)
            continue  # 缺少信息跳过

        save_path = safe_download(url, save_dir, sku)
        if save_path:
            success_count += 1
            df.at[idx, image_column] = os.path.abspath(save_path)
        else:
            fail_count += 1

        pbar_image_download.set_postfix({"成功": success_count, "失败": fail_count})
        pbar_image_download.update(1)

    pbar_image_download.close()
    # 保存 Excel
    out_path = out_excel_path or config["out_filename"]
    df.to_excel(out_path, index=False)
    print(f"图片下载完成，保存到 Excel: {out_path}")


def parse_page(page: ChromiumPage):
    """健壮版解析函数，支持局部刷新重试"""
    index = 1

    while index <= config["max_products"]:
        try:

            pagination = page.ele("xpath:.//span[@role='link' and @aria-current='true']")  # 当前页
            next_pagination = pagination.ele("xpath:./following-sibling::*[1]")  # 下一页

            # 每次循环都重新找 div_main，避免缓存元素失效
            div_main = page.ele("@role=main", timeout=5)
            if not div_main:
                print("未找到 div_main，等待刷新...")
                page.wait(1)
                continue

            # 找商品组合
            product_list = div_main.ele("xpath:./div[contains(@class, 'product-list')]", timeout=5)

            product_divs = product_list.eles("xpath:./div[contains(@class, 'product-card')]", timeout=5)

            for product_div in product_divs:
                # 判断是否已处理过
                if product_div.attr("data-grabbed") == "1":
                    continue

                product_info = {
                    "index": index,
                    "sku": "",
                    "title": "",
                    "price": "",
                    "img_url": "",
                    "product_url": ""
                }

                try:
                    a_product = product_div.ele("tag:a", timeout=2)
                    if a_product:
                        href = a_product.attr("href")
                        sku = a_product.attr("data-sku")
                        title = a_product.attr("data-title")
                        price = a_product.attr("data-price")

                        product_info["product_url"] = href
                        product_info["sku"] = sku
                        product_info["title"] = title
                        product_info["price"] = price

                    img = product_div.ele("tag:img", timeout=2)
                    if img:
                        product_info["img_url"] = img.attr("src")

                    yield product_info

                    # 加标记，避免重复处理
                    product_div.run_js("this.style.backgroundColor = 'lightblue';")
                    index += 1
                    if index > config["max_products"]:
                        return

                except Exception as e:
                    print(f"处理 product_card 出错，跳过: {e}")
                    continue

                # 给整个 grid 打标记
                product_div.run_js("this.setAttribute('data-grabbed', '1');")

                # 跟随滑动
                if index % 4 == 0:
                    product_div.run_js("this.scrollIntoView({behavior: 'smooth', block: 'center'});")
                    page.wait(config["scroll_pause"])

            # 加载更多
            if next_pagination:
                next_pagination.click()
            page.wait(config["scroll_pause"])

        except Exception as e:
            # 捕获 ElementLostError 等异常，等待后重试
            print(f"parse_page 遇到异常: {e}，重试中...")
            page.wait(1)
            continue


if __name__ == "__main__":

    print("这是一个可视化的网页数据抓取工具，专门用于抓取 Ozon.ru 上的产品信息，自定义数量，可选择下载、插入图片到表格中")
    print("""
    将会抓取以下字段：
        index           商品排序
        sku             SKU
        title           标题
        price           价格
        img_url         首图图片地址（如果插入图片此处将被替换为图片）
        product_url     产品详情页面
        
    """)

    main_page = ChromiumPage()
    main_page.get(config["url"])
    print("网页打开成功")

    if os.path.exists(config["out_filename"]):
        now = datetime.now()
        config["out_filename"] = now.strftime("结果_%Y%m%d_%H%M%S.xlsx")

    config["max_products"] = int(
        input(f"输入需要抓取的数量，页面数量不足时将会自动翻页（默认 {config['max_products']} 个）：") or config[
            "max_products"]
    )

    # config["download_image"] = questionary.select(
    #     "是否下载图片？",
    #     choices=[
    #         questionary.Choice("Yes", value=True),
    #         questionary.Choice("No", value=False)
    #     ]
    # ).ask()
    # if config["download_image"]:
    #     config["insert_image"] = questionary.select(
    #         "是否将图片插入表格？（不插入表格将会用图片下载的本地路径表示）",
    #         choices=[
    #             questionary.Choice("Yes", value=True),
    #             questionary.Choice("No", value=False)
    #         ]
    #     ).ask()

    input("请在网页中进行搜索/筛选/登录操作后，按回车开始抓取数据...")

    all_tabs = main_page.browser.get_tabs()
    if not all_tabs:
        print("没有找到可用标签页！")
        exit(1)

    if len(all_tabs) > 1:
        input("请保留需要抓取的唯一页面，关闭其他页面...")

    main_page = all_tabs[0]

    print(f"Page Title: {main_page.title}")
    print("正在抓取数据，请勿操作页面！")

    pbar = tqdm(total=config["max_products"], desc="进度")
    batch = []
    for product in parse_page(main_page):
        batch.append(product)
        pbar.update(1)
        if len(batch) >= config["batch_size"]:
            append_to_excel(batch)
            batch.clear()

    if batch:
        append_to_excel(batch)

    pbar.close()

    print(f"结果已经保存至 {config["out_filename"]}")

    if config["download_image"]:
        download_images_from_excel()

    if config["insert_image"]:
        insert_images_from_column(file_path=config["out_filename"], image_col="E")

    input("按任意键关闭程序...")
