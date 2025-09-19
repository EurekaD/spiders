import re
import time
from datetime import datetime
import traceback
from DrissionPage import ChromiumPage
from dateutil.relativedelta import relativedelta

RUB_TO_CNY = 0.085  # 1 卢布 ≈ 0.075 人民币

extract_num = lambda s: re.search(r"\d+", s).group() if re.search(r"\d+", s) else None

extract_rating = lambda s: float(re.match(r"([\d.,]+)", s.strip()).group(1).replace(",", "."))


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

        return product_data

    except Exception as e:
        traceback.print_exc()


if __name__ == "__main__":
    main_page = ChromiumPage()

    url = "https://www.ozon.ru/product/kovrik-naduvnoy-turisticheskiy-penka-karemat-matras-2065642899/"

    product_data = parse_product_page(main_page, url, "test.xlsx")

    for k, v in product_data.items():
        print(f"{k}: {v}")

