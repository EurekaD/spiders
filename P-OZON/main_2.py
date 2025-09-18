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
import re
import time
from datetime import datetime
import pandas as pd
from queue import Queue, Empty
from DrissionPage import ChromiumPage
from concurrent.futures import ThreadPoolExecutor, as_completed
import traceback
from dateutil.relativedelta import relativedelta

# 全局配置
config = {
    "url": r"https://www.ozon.ru/product",  # 要抓取的网页地址
    "out_filename": "结果.xlsx",  # 输出 Excel 文件名
    "image_dir": "图片",  # 图片保存目录
    "max_workers": 2,  # 最大并发线程数，未使用多线程
    "batch_size": 20,  # 每批次写入 Excel 的数据条数
    "max_products": 20,  # 最大抓取的产品数量，用户可修改
    "scroll_pause": 1,  # 每次下滑等待加载的秒数
    "download_image": False,  # 是否下载图片
    "insert_image": False,  # 是否将图片插入表格
}


RUB_TO_CNY = 0.085  # 1 卢布 ≈ 0.075 人民币

extract_num = lambda s: re.search(r"\d+", s).group() if re.search(r"\d+", s) else None

extract_rating = lambda s: (
    float(m.group(1).replace(",", ".")) if (m := re.search(r"([\d.,]+)", s or "")) else None
)


def now_str():
    # 格式: 2025/09/18 21:05:32
    return datetime.now().strftime("%Y/%m/%d %H:%M:%S")


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


def extract_seller_from_href(href_str: str) -> str | None:
    """从 href 中提取 SKU"""
    try:
        m = re.search(r"/seller/([^/]+)/?", href_str)
        if not m:
            return None
        slug = m.group(1)
        seller_id_str = slug.split("-")[-1]
        return seller_id_str
    except Exception as e:
        print(e)
        return None


def append_to_excel(data: dict | list[dict], filename: str = None):
    """
    将字典或字典列表追加到 Excel 文件中。
    - data: 单个 dict 或多个 dict (list[dict])
    - filename: Excel 文件路径
    """
    if not filename:
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


def parse_sellers_page(page: ChromiumPage):
    sellers = []

    div_webBestSeller = page.ele('@data-widget=webBestSeller', timeout=5)
    if div_webBestSeller:
        button_webBestSeller = div_webBestSeller.ele('tag:button')

        if button_webBestSeller:
            button_webBestSeller.click()
            print("点击跟卖 查看更多")

            time.sleep(5)

            div_sellerList = page.ele('#seller-list', timeout=5)

            if div_sellerList:
                button_more_sellerList = div_sellerList.ele("xpath:./button", timeout=5)

                if button_more_sellerList:
                    button_more_sellerList.click()
                    print("点击更多 显示全部")

                    # 暂存所有的商家链接
                    div_sellers = div_sellerList.eles("xpath:./div/div", timeout=5)

                    for div_seller in div_sellers:
                        a_seller = div_seller.ele("xpath:./div/div[2]//a")
                        if a_seller:
                            seller_url = a_seller.attr("href")
                            seller_name = a_seller.text

                            print(f"{seller_name} : {seller_url}")
                            sellers.append(
                                {
                                    "seller_name": seller_name,
                                    "url": seller_url,
                                    "is_processed": 0
                                }
                            )

    print(f"找到 {len(sellers)} 家跟卖， 依次抓取这些商家的所有商品")
    append_to_excel(sellers, filename="sellers.xlsx")
    return sellers


def parse_seller_page(page: ChromiumPage):
    """健壮版解析函数，支持局部刷新重试"""
    index = 1

    while index <= config["max_products"]:
        try:
            # 每次循环都重新找 paginator，避免缓存元素失效
            paginator = page.ele("#paginator", timeout=5)
            if not paginator:
                print("未找到 paginator，等待刷新...")
                page.wait(1)
                continue

            # 找商品网格
            product_grids = paginator.eles('@data-widget=tileGridDesktop', timeout=5)

            for grid in product_grids:
                # 判断是否已处理过
                if grid.attr("data-grabbed") == "1":
                    continue

                product_cards = grid.children(timeout=5)

                for product_card in product_cards:
                    product_info = {
                        "index": index,
                        "sku": "",
                        "title": "",
                        "price": "",
                        "img_url": "",
                        "product_url": ""
                    }

                    try:
                        a_product = product_card.ele("tag:a", timeout=2)
                        if a_product:
                            href = a_product.attr("href")
                            sku = extract_sku_from_href(href)
                            product_info["product_url"] = href
                            product_info["sku"] = sku

                        span_price = product_card.ele("xpath:./div", timeout=2).ele("tag:span", timeout=2)
                        if span_price:
                            product_info["price"] = span_price.text

                        a_title = product_card.ele("xpath:./div", timeout=2).ele("tag:a", timeout=2)
                        if a_title:
                            product_info["title"] = a_title.text

                        img = product_card.ele("tag:img", timeout=2)
                        if img:
                            product_info["img_url"] = img.attr("src")

                        yield product_info

                        # 加标记，避免重复处理
                        product_card.run_js("this.style.backgroundColor = 'lightblue';")
                        index += 1
                        if index > config["max_products"]:
                            return

                    except Exception as e:
                        print(f"处理 product_card 出错，跳过: {e}")
                        continue

                # 给整个 grid 打标记
                grid.run_js("this.setAttribute('data-grabbed', '1');")

            # 下滑加载更多
            page.run_js("window.scrollBy(0, document.body.scrollHeight);")
            page.wait(config["scroll_pause"])

        except Exception as e:
            # 捕获 ElementLostError 等异常，等待后重试
            print(f"parse_page 遇到异常: {e}，重试中...")
            page.wait(1)
            continue


def get_recent_reviews(tab, timestamp_sec, scroll_pause=1):
    """
    滚动加载并统计 timestamp_sec 之后的评论数量
    :param tab: DrissionPage 元素（评论列表容器）
    :param timestamp_sec: 时间戳阈值
    :param scroll_pause: 每次滚动后的等待时间
    :return: reviews_timestamp 列表, 数量
    """
    reviews_timestamp = []
    seen_ids = set()  # 防止重复

    # 找到评论区域
    review_tab = tab.ele('@data-widget=webReviewTabs', timeout=5)
    if not review_tab:
        raise RuntimeError("未找到评论区域")

    # 先滚到评论区域
    review_tab.scroll.to_see()
    time.sleep(scroll_pause)

    while True:
        # 获取当前加载的评论
        div_reviews = tab.eles('@publishedat', timeout=5)
        new_reviews = []
        for div in div_reviews:
            ts = int(div.attr("publishedat"))
            if ts > timestamp_sec and ts not in seen_ids:
                new_reviews.append(ts)
                seen_ids.add(ts)

        if not new_reviews:
            # 没有新评论了，停止滚动
            break

        reviews_timestamp.extend(new_reviews)

        # 滚动评论区域，触发更多评论加载
        review_tab.scroll.to_bottom()
        time.sleep(scroll_pause)

    sales_volume = len(reviews_timestamp)
    return reviews_timestamp, sales_volume


def parse_product_page(page: ChromiumPage, url: str, filename: str):
    """解析具体的产品详情页"""
    try:
        tab = page.new_tab(url=url)

        # 等待页面加载
        tab.wait.load_start()
        time.sleep(1)

        product_id = ""               # 商品Id
        primary_category = ""         # 一级类目
        secondary_category = ""       # 二级类目
        tertiary_category = ""        # 三级类目
        green_price_rub = ""          # 绿标价（卢布）
        green_price_cny = ""          # 绿标价（￥）
        black_price_rub = ""          # 黑标价（卢布）
        black_price_cny = ""          # 黑标价（￥）
        lowest_follow_price_cny = ""  # 跟卖最低价（￥）
        sales_volume = 0              # 销量
        follow_seller_count = ""      # 跟卖数量
        product_rating = ""           # 商品评分
        product_link = ""             # 商品链接
        country_of_origin = ""        # 商品生产国家
        product_info = {}             # 商品信息
        first_crawled_at = ""         # 商品数据首次获取时间
        last_updated_at = ""          # 商品数据更新时间

        button_sku = tab.ele("@data-widget=webDetailSKU", timeout=5)
        if button_sku:
            div_sku = button_sku.ele("xpath:./div")
            if div_sku:
                sku_str = div_sku.text
                product_id = extract_num(sku_str)

        div_breadCrumbs = tab.ele('@data-widget=breadCrumbs', timeout=5)
        if div_breadCrumbs:
            li_primary_category = div_breadCrumbs.ele("xpath:./ol/li[1]")
            li_secondary_category = div_breadCrumbs.ele("xpath:./ol/li[2]")
            li_tertiary_category = div_breadCrumbs.ele("xpath:./ol/li[3]")

            if li_primary_category:
                primary_category = li_primary_category.text
            if li_secondary_category:
                secondary_category = li_secondary_category.text
            if li_tertiary_category:
                tertiary_category = li_tertiary_category.text

        div_webPrice = tab.ele('@data-widget=webPrice', timeout=5)
        if div_webPrice:
            span_green_price = div_webPrice.ele(
                'xpath://span[contains(text(), "c Ozon Картой")]/preceding-sibling::div/span', timeout=5)
            span_black_price = div_webPrice.ele(
                'xpath://div[span[contains(text(), "без Ozon Карты")]]/preceding-sibling::div/span[1]', timeout=5)

            if span_green_price:
                green_price_rub = span_green_price.text
                num_str = ''.join(re.findall(r'\d+', green_price_rub))
                amount_rub = float(num_str)
                green_price_cny = round(RUB_TO_CNY * amount_rub, 2)

            if span_black_price:
                black_price_rub = span_black_price.text
                num_str = ''.join(re.findall(r'\d+', black_price_rub))
                amount_rub = float(num_str)
                black_price_cny = round(RUB_TO_CNY * amount_rub, 2)

        div_webBestSeller = tab.ele('@data-widget=webBestSeller', timeout=5)
        if div_webBestSeller:
            span_lowest_price = div_webBestSeller.ele('xpath://span[contains(text(), "от")]')
            if span_lowest_price:
                lowest_price = span_lowest_price.text
                num_str = ''.join(re.findall(r'\d+', lowest_price))
                amount_rub = float(num_str)
                lowest_follow_price_cny = round(RUB_TO_CNY * amount_rub, 2)

            div_follow_seller_count = div_webBestSeller.ele('xpath:./div/button/span/div/div[2]')
            if div_follow_seller_count:
                follow_seller_count = div_follow_seller_count.text

        one_month_ago = datetime.now() - relativedelta(months=1)
        timestamp_sec = int(one_month_ago.timestamp())

        reviews_timestamp, sales_volume = get_recent_reviews(tab, timestamp_sec)
        print(reviews_timestamp)

        div_webSingleProductScore = tab.ele('@data-widget=webSingleProductScore', timeout=5)
        if div_webSingleProductScore:
            score_str = div_webSingleProductScore.text
            if score_str:
                product_rating = extract_rating(score_str)

        product_link = url

        span_address = tab.ele('xpath://span[contains(text(), "Со склада продавца")]')
        if span_address:
            address = span_address.text
            country_of_origin = address.split(",")[-1]

        div_webShortCharacteristics = tab.ele('@data-widget=webShortCharacteristics', timeout=5)
        if div_webShortCharacteristics:
            divs_info = div_webShortCharacteristics.eles('xpath:./div[2]/div')

            for div_info in divs_info:
                div_info_key = div_info.ele('xpath:./div[1]')
                div_info_value = div_info.ele('xpath:./div[2]')
                if div_info_key and div_info_value:
                    product_info[div_info_key.text] = div_info_value.text

        product_data = {
            "product_id": product_id,
            "primary_category": primary_category,
            "secondary_category": secondary_category,
            "tertiary_category": tertiary_category,
            "green_price_rub": green_price_rub,
            "green_price_cny": green_price_cny,
            "black_price_rub": black_price_rub,
            "black_price_cny": black_price_cny,
            "lowest_follow_price_cny": lowest_follow_price_cny,
            "sales_volume": sales_volume,
            "follow_seller_count": follow_seller_count,
            "product_rating": product_rating,
            "product_link": product_link,
            "country_of_origin": country_of_origin,
            "product_info": product_info,
            "first_crawled_at": now_str(),
            "last_updated_at": now_str(),
        }
        tab.close()
        return product_data

    except Exception as e:
        traceback.print_exc()


def worker(worker_index: int):
    # 每个线程单独的 ChromiumPage
    page = ChromiumPage()
    output_filename_worker = f"worker_{worker_index}.xlsx"
    while not task_queue.empty():
        try:
            index, url = task_queue.get_nowait()

            product_data = parse_product_page(page, url=url, filename=output_filename_worker)

            append_to_excel(product_data, output_filename_worker)

            task_queue.task_done()
        except Empty:
            break
        except Exception as e:
            print(f"线程异常: {e}")
    # page.quit()


if __name__ == "__main__":
    print(
        "这是一个可视化的网页数据抓取工具，用于抓取 Ozon.ru 上的产品信息，对于你选定的商品，遍历所有跟卖商家，抓取他们的所有商品，输出到表格中")
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

    sellers_file = f"sellers.xlsx"
    if not os.path.exists(sellers_file):
        parse_sellers_page(main_page)

    df_sellers = pd.read_excel(sellers_file)
    sellers = df_sellers["url"]

    seller_product_file = f"sellers_products.xlsx"
    if not os.path.exists(seller_product_file):
        for seller in sellers:
            print(f"正在寻找商家 {seller['seller_name']} 的产品集合...")

            main_page.get(seller["url"])

            batch = []
            for product in parse_seller_page(main_page):
                product["seller_id"] = extract_seller_from_href(seller["url"])
                batch.append(product)
                if len(batch) >= config["batch_size"]:
                    append_to_excel(batch, filename=seller_product_file)
                    batch.clear()
            if batch:
                append_to_excel(batch, filename=seller_product_file)

    print("开始抓取具体的商品详情")
    # 抓取具体商品
    product_links = []
    if os.path.exists(seller_product_file):
        df_products = pd.read_excel(seller_product_file)
        product_links = df_products["product_url"].tolist()
    else:
        print("Error")

    print(f"找到 {len(product_links)} 个产品链接")

    tasks = list(enumerate(product_links))
    task_queue = Queue()
    for index, url in tasks:
        task_queue.put((index, url))

    with ThreadPoolExecutor(max_workers=config["max_workers"]) as executor:
        for worker_index in range(config["max_workers"]):
            executor.submit(worker, worker_index)









