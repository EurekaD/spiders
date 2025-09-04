from DrissionPage import ChromiumPage
import requests
from bs4 import BeautifulSoup
import re
import io
import pandas as pd
from glob import glob
from openpyxl import load_workbook
from openpyxl.drawing.image import Image as DrawingImage
from PIL import Image as PILImage
import os


OUTPUT_FILENAME = "结果.xlsx"
IMAGE_DIR = "图片"

if __name__ == "__main__":

    if not os.path.exists(IMAGE_DIR):
        os.makedirs(IMAGE_DIR)
        print(f"创建图片目录: ./{IMAGE_DIR}")

    # 创建结果表格，中途禁止用户打开，可以每100个输出到临时表格中，以便随时进行查看

    # Step 1 打开网页
    page = ChromiumPage()
    page.get(r"https://www.ozon.ru/product")
    print("网页打开成功")

    # 输入需要的数量
    max_products = int(input("输入需要抓取的产品数量（默认100个）：") or 100)

    # Step 2 等待用户操作网页 输入搜素词，筛选，登录等
    input("请输入搜索词或者进行筛选、登录等操作,准备完成后，按回车开始抓取数据..................")

    # 用户点击确认后开始抓取
    context = page.




