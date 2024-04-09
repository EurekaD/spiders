# -*- coding: utf-8 -*-
"""
日期：2024-04-05 10:22:03
文件路径：其他任务/自建项目/招聘题目/1_第一题_登录认证.py
作者：祖世辉
功能：
考察点：
    请求添加用户登录验证信息。
    从页面提取信息的能力
"""
import json
import threading

from lxml import etree
from addict import Dict
import urllib.parse
import os

import requests

proxy_none = {
    'http': "http://localhost:7890",
    'https': "https://localhost:7890"
}


class scrape():
    base_url = 'https://ssr3.scrape.center'
    proxy = proxy_none

    header = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Authorization': 'Basic YWRtaW46YWRtaW4=',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Referer': 'https://ssr3.scrape.center/page/1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.160 Safari/537.36',
            'sec-ch-ua': '"Chromium";v="119", "Not?A_Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }

    def __init__(self):
        self.data_url_list = []  # 保存列表页数据
        self.write_file_lock = threading.Lock()

    def get_url_list(self,page) -> [list,None]:
        """
        获取列表页的信息
        :param self:
        :param url: 列表页url
        :return: list[dict]  列表套字典的形式返回列表信息
        """

        try:
            r = requests.get(f'https://ssr3.scrape.center/page/{page}', headers=self.header,proxies=self.proxy)

            print(r.status_code)
            # print(r.text)

            tree = etree.HTML(r.text)

            r_list = []
            div_list = tree.xpath('//div[@class="el-card item m-t is-hover-shadow"]')
            for div in div_list:
                tem_dict = Dict({})
                title = div.xpath('.//h2[@class="m-b-sm"]/text()')
                title = title[0].strip() if len(title) > 0 else ''
                tem_dict.title = title

                a_url = div.xpath('.//a[@class="name"]/@href')
                a_url = a_url[0] if len(a_url) > 0 else ''
                tem_dict.url = self.base_url + a_url

                categories = div.xpath('.//div[@class="categories"]//span/text()')
                categories = ','.join(categories)
                tem_dict.categories = categories

                info1 = div.xpath('.//div[@class="m-v-sm info"][1]/span/text()')
                if len(info1) > 2:
                    tem_dict.country = info1[0].strip()
                    tem_dict.runtime = info1[2].strip()

                release_date = div.xpath('.//div[@class="m-v-sm info"][2]/span/text()')
                release_date = release_date[0] if len(release_date) > 0 else ''
                tem_dict.release_date = release_date



                score = div.xpath('.//p[@class="score m-t-md m-b-n-sm"]/text()')
                score = score[0].strip() if len(score) > 0 else ''
                tem_dict.score = score

                print(tem_dict)
                r_list.append(tem_dict)

            if r_list:
                return r_list


        except Exception as e:
            print('获取列表页报错：',str(e))

            import traceback
            print(traceback.format_exc())
            return None


    def get_content(self,url):
        """
        获取某一个电影的详细信息
        :param url:
        :return:
        """
        r = requests.get(url, headers=self.header,proxies=self.proxy)

        print(r.status_code)
        # print(r.text)
        tree = etree.HTML(r.text)
        tem_dict = Dict({})
        desc = tree.xpath('//div[@class="drama"]//p/text()')
        desc = desc[0] if len(desc) > 0 else ''
        desc = desc.strip()
        tem_dict.desc = desc


        director = tree.xpath('//div[@class="directors el-row"]//div[@class="el-card__body"]/p/text()')
        director = ' '.join(director) if len(director) > 0 else ''
        tem_dict.director = director

        div_actors = tree.xpath('//div[@class="actors el-row"]//div[@class="el-card__body"]')
        if div_actors:
            tem_dict.actors = []
            for actor in div_actors:
                ps = actor.xpath('.//p/text()')
                actor_info = ' '.join(ps)
                if actor_info:
                    tem_dict.actors.append(actor_info)
        print(tem_dict)
        if desc:
            # 保留页面源码
            self.save_html_file(url, r.text)
            return tem_dict

    @staticmethod
    def save_html_file(url, content, base_path='html'):
        """
        保存获取到的页面源码到文件
        :param url: 页面地址，转换后当做文件名
        :param content:页面html内容
        :param base_path: 文件保存地址，默认当前目录下的html目录
        :return:
        """
        if not os.path.exists(base_path):
            os.makedirs(base_path)

        encoded_url = urllib.parse.quote(url).replace("/", "%2F") + '.html'
        with open(os.path.join(base_path, encoded_url),encoding='utf-8',mode='a') as f:
            print(content,file=f)

    def add_data_to_file(self,file_path,data):
        """ 文件地址尽量写全局地址 """
        self.write_file_lock.acquire()  # 获取锁
        try:
            with open(file_path,encoding='utf-8',mode='a') as f:
                print(data,file=f)
        finally:
            self.write_file_lock.release()

    def get_url_list_start(self):
        """
        调度  获取所有列表页数据，并把数据记录到文件中。 如果有失败的，设置重试
        :return:  列表页信息
        """
        err_url_list = []  # 失败的信息记录

        for page in range(1,11):
            data_list = self.get_url_list(page)
            if data_list:
                self.data_url_list.extend(data_list)
            else:
                err_url_list.append(page)

        # 设置失败重试  重试三次
        for i in range(3):
            for _ in range(len(err_url_list)):
                page = err_url_list.pop()
                data_list = self.get_url_list(page)
                if data_list:
                    self.data_url_list.extend(data_list)
                else:
                    err_url_list.append(page)

        # 防止数据丢失 文件保存
        with open('列表页数据.json','a',encoding='utf-8') as f:
            for data in self.data_url_list:
                print(json.dumps(data,ensure_ascii=False),file=f)

        # 如果仍有失败的，保存到文件
        if err_url_list:
            with open('列表页调用失败页数.json','a',encoding='utf-8') as f:
                for data in err_url_list:
                    print(data,file=f)


    def get_content_start(self):
        """
        调度  获取所有详情页数据，并把数据记录到文件中。 如果有失败的，设置重试
        :return: 详情页信息
        """
        err_info_list = []

        for info in self.data_url_list:
            url = info['url']
            data_dict = self.get_content(url)
            if data_dict:
                info.update(data_dict)
                self.add_data_to_file('电影信息.json',json.dumps(info,ensure_ascii=False))
            else:
                err_info_list.append(info)

        # 设置失败重试  重试三次
        for i in range(3):
            for _ in range(len(err_info_list)):
                info = err_info_list.pop()
                url = info['url']
                data_dict = self.get_content(url)
                if data_dict:
                    info.update(data_dict)
                    self.add_data_to_file('电影信息.json', json.dumps(info, ensure_ascii=False))
                else:
                    err_info_list.append(info)


        # 如果仍有失败的，保存到文件
        if err_info_list:
            with open('详情页调用失败信息.json', 'a', encoding='utf-8') as f:
                for data in err_info_list:
                    print(json.dumps(data, ensure_ascii=False), file=f)

    def start(self):
        self.get_url_list_start()
        self.get_content_start()


if __name__ == '__main__':
    ss = scrape()
    ss.start()
