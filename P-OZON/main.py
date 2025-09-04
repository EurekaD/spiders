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




output_filename = "结果.xlsx"
image_dir = "图片"

if __name__ == "__main__":

    if not os.path.exists(image_dir):
        os.makedirs(image_dir)
        print(f"创建图片目录: {image_dir}")


    # Step 1 打开网页
    pass

    # Step 2 等待用户操作网页 输入搜素词，筛选，登录等
    # 输入需要的数量
    # 用户点击确认后开始抓取

    # Step 3 开始抓取数据

    # Step 4

