# -*- coding: utf-8 -*-
"""
日期：2024-04-05 11:48:15
文件路径：其他任务/自建项目/招聘题目/2_第二题_页面分析.py
作者：祖世辉
功能：
"""
"""
目标网站：
https://www.xinpianchang.com/discover/article-27-180

要求：
    获取七张列表页中的所有视频元信息信息，包含：标题、分类、作者
    获取视频下载链接，并下载最低画质的视频内容
"""

import re
import shutil
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


class xinpianchang():
    base_url = 'https://www.xinpianchang.com/'
    proxy = proxy_none

    headers = {
        'authority': 'www.xinpianchang.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'zh-CN,zh;q=0.9',
        'cache-control': 'max-age=0',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.160 Safari/537.36',
    }
    cookies = {
        'Hm_lvt_446567e1546b322b726d54ed9b5ad346': '1709290211',
        'Device_ID': '65e1b2e289f329162',
        'Authorization': 'D882D4BFB2F6F4E24B2F6F4F98B2F6F870DB2F6F94A7FFC3FCA7',
        'sajssdk_2015_cross_new_user': '1',
        'sl-session': 'm2qILgQF42VkegEXrhPTDg==',
        'PHPSESSID': 'k0j4d7ip2v264ec79l5ucum4je',
        'visited': '2024-3-1',
        'sensorsdata2015jssdkcross': '%7B%22distinct_id%22%3A%2214500489%22%2C%22first_id%22%3A%2218df9a2ce1259d-013f59b0131a7a6-4c657b58-2073600-18df9a2ce1310e2%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%2C%22%24latest_utm_source%22%3A%22eduWeb%22%2C%22%24latest_utm_medium%22%3A%22eduListCover%22%7D%2C%22%24device_id%22%3A%2218df9a2ce1259d-013f59b0131a7a6-4c657b58-2073600-18df9a2ce1310e2%22%7D',
        'Hm_lpvt_446567e1546b322b726d54ed9b5ad346': '1709291779',
    }

    def __init__(self):
        self.data_url_info_list = []  # 保存列表页数据
        self.write_file_lock = threading.Lock()

    def get_url_list(self, page_url):

        try:
            r = requests.get('https://www.xinpianchang.com/discover/article-27-180', verify=False, cookies=self.cookies, headers=self.headers, proxies=self.proxy)
            print(r.status_code)
            # print(r.text)
            r_list = []
            tree = etree.HTML(r.text)
            div_list = tree.xpath(
                '//main//div[@class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 3xl:grid-cols-5 4xl:grid-cols-6 gap-4"]/div')
            for div in div_list:
                title = div.xpath('./div[@class="min-h-[96px]"]//a[1]/@title')
                url = div.xpath('./div[@class="min-h-[96px]"]//a[1]/@href')
                video_type = div.xpath(
                    './div[@class="min-h-[96px]"]/div[@class="px-3 text-xs h-4.5 text-gray-400"]//text()')

                title = title[0].strip() if len(title) > 0 else ''
                url = url[0].strip() if len(url) > 0 else ''
                video_type = ''.join(video_type) if len(video_type) > 0 else ''

                if url:
                    data_dict = {
                        'title': title,
                        'page_url': page_url,
                        'url': url,
                        'video_type': video_type,
                    }
                    r_list.append(data_dict)
            # print(r_list)
            if len(r_list) > 0:

                return r_list
        except Exception as e:
            print('获取列表页报错：', str(e))
            return None

    def get_url_list_start(self):
        """
        调度  获取所有列表页数据，并把数据记录到文件中。 如果有失败的，设置重试
        :return:  列表页信息
        """
        err_url_list = []  # 失败的信息记录

        url_first = 'https://www.xinpianchang.com/discover/article-27-180'
        url_list = [url_first]
        for page in range(2,8):
            url = f'{url_first}-all-all-0-0-score-pp{page}'
            url_list.append(url)

        for url in url_list:
            data_list = self.get_url_list(url)
            print(data_list)
            if data_list:
                self.data_url_info_list.extend(data_list)
            else:
                err_url_list.append(url)

        # 设置失败重试  重试三次
        for i in range(3):
            for _ in range(len(err_url_list)):
                page = err_url_list.pop()
                data_list = self.get_url_list(page)
                if data_list:
                    self.data_url_info_list.extend(data_list)
                else:
                    err_url_list.append(page)

        # 防止数据丢失 文件保存
        with open('列表页数据.json','a',encoding='utf-8') as f:
            for data in self.data_url_info_list:
                print(json.dumps(data,ensure_ascii=False),file=f)

        # 如果仍有失败的，保存到文件
        if err_url_list:
            with open('列表页调用失败页数.json','a',encoding='utf-8') as f:
                for data in err_url_list:
                    print(data,file=f)

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

    def get_video_info_url(self,url):
        """
        从详情页获取 一个视频信息接口url
        :param url: 详情页 url
        :return: 视频信息接口url
        """
        cookies = {
            'Hm_lvt_446567e1546b322b726d54ed9b5ad346': '1709290211',
            'Device_ID': '65e1b2e289f329162',
            'Authorization': 'D882D4BFB2F6F4E24B2F6F4F98B2F6F870DB2F6F94A7FFC3FCA7',
            'sajssdk_2015_cross_new_user': '1',
            'sl-session': 'm2qILgQF42VkegEXrhPTDg==',
            'PHPSESSID': 'k0j4d7ip2v264ec79l5ucum4je',
            'visited': '2024-3-1',
            'sensorsdata2015jssdkcross': '%7B%22distinct_id%22%3A%2214500489%22%2C%22first_id%22%3A%2218df9a2ce1259d-013f59b0131a7a6-4c657b58-2073600-18df9a2ce1310e2%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%2C%22%24latest_utm_source%22%3A%22eduWeb%22%2C%22%24latest_utm_medium%22%3A%22eduListCover%22%7D%2C%22%24device_id%22%3A%2218df9a2ce1259d-013f59b0131a7a6-4c657b58-2073600-18df9a2ce1310e2%22%7D',
            'Hm_lpvt_446567e1546b322b726d54ed9b5ad346': '1709293746',
        }
        try:
            r = requests.get(url,cookies=self.cookies, headers=self.headers,proxies=self.proxy,timeout=60)
            r.encoding = r.apparent_encoding
            print(r.status_code)
            # print(r.text)

            # 使用正则表达式提取字典内容
            match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', r.text)
            if match:
                dict_str = match.group(1)
                try:
                    data = json.loads(dict_str)
                    # print(dict_str)
                    # print(data)

                    video_library_id = data['props']['pageProps']['detail']['video_library_id']
                    if video_library_id:
                        vider_info_url = f'https://mod-api.xinpianchang.com/mod/api/v2/media/{video_library_id}?appKey=61a2f329348b3bf77&extend=userInfo%2CuserStatus'
                        self.save_html_file(url, r.text)
                        print(vider_info_url)
                        return vider_info_url
                except Exception as e:
                    print('解析失败：', str(e))

        except Exception as e:
            print('获取详情页报错：', str(e))
            return None


    def get_video_dl_url_info(self,get_url):
        """
        获取
        :param get_url: 视频信息接口
        :return: 视频下载链接 信息
        """
        try:
            r = requests.get(get_url, cookies=self.cookies, headers=self.headers, proxies=self.proxy, timeout=60)
            r.encoding = r.apparent_encoding
            print(r.status_code)
            r_json = r.json()

            video_url = ''
            url_infos = r_json['data']['resource']['progressive']
            for url_info in url_infos:
                profile = url_info['profile']
                backupUrl = url_info['backupUrl']

                if '360' in profile:
                    video_url = backupUrl
                if not video_url and '720' in profile:
                    video_url = backupUrl
                if not video_url and '1080' in profile:
                    video_url = backupUrl

            if not video_url:
                video_url = url_infos[0]['backupUrl']

            if video_url:
                data_dict = {
                    'video_dl_url': video_url,
                    'url_infos': url_infos,
                }
                print(data_dict)
                is_true = True

                # 保存 json信息
                r_json['from_url'] = get_url
                self.add_data_to_file('视频信息接口数据.json',json.dumps(r_json, ensure_ascii=False))

                return data_dict

        except Exception as e:
            print('获取地址失败：', str(e))


    def get_video_info_start(self):
        self.get_url_list_start()  # 获取所有的列表页信息

        err_info = []

        for info in self.data_url_info_list:
            url = info['url']

            for _ in range(3):
                vider_info_url = self.get_video_info_url(url)
                if vider_info_url:
                    info['vider_info_url'] = vider_info_url
                    break
            if info.get('vider_info_url'):
                #获取视频信息
                for _ in range(3):
                    video_info = self.get_video_dl_url_info(info['vider_info_url'])
                    if video_info:
                        info.update(video_info)
                        break

            if info.get('video_dl_url'):
                self.add_data_to_file('新片场_info.json',json.dumps(info, ensure_ascii=False))
            else:
                err_info.append(info)

        # 设置失败重试  重试三次
        for i in range(3):
            for _ in range(len(err_info)):
                info = err_info.pop()
                url = info['url']

                for _ in range(3):
                    vider_info_url = self.get_video_info_url(url)
                    if vider_info_url:
                        info['vider_info_url'] = vider_info_url
                        break
                if info['video_url']:
                    # 获取视频信息
                    for _ in range(3):
                        video_info = self.get_video_dl_url_info(info['vider_info_url'])
                        if video_info:
                            info.update(video_info)
                            break

                if info.get('video_dl_url'):
                    self.add_data_to_file('新片场_info.json', json.dumps(info, ensure_ascii=False))
                else:
                    err_info.append(info)

        # 如果仍有失败的，保存到文件
        if err_info:
            with open('详情页调用失败信息.json', 'a', encoding='utf-8') as f:
                for data in err_info:
                    print(json.dumps(data, ensure_ascii=False), file=f)


    def video_dl(self,video_dl_url,base_path='mp4'):
        """
        下载视频
        :param video_dl_url:
        :return:
        """
        if not os.path.exists(base_path):
            os.mkdir(base_path)
        try:
            r = requests.get(video_dl_url, headers=self.headers, proxies=self.proxy, timeout=60 * 15, stream=True)
            print(r.status_code)
            if r.status_code == 200:
                file_name = video_dl_url.split('/')[-1]
                file_name = file_name.split('.mp4')[0] + '.mp4'
                tem_path = os.path.join(base_path, 'tem')
                if not os.path.exists(tem_path):
                    os.mkdir(tem_path)
                file_path = os.path.join(base_path, file_name)
                file_tem_path = os.path.join(tem_path, file_name)
                print('文件保存路径 --------------- ', file_tem_path)

                with open(file_tem_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024 * 10):
                        if chunk:
                            f.write(chunk)

                # 将文件从tem文件夹转移到指定为止
                shutil.move(file_tem_path, base_path)
                print('视频下载成功 -------------- ', file_path)
                return True

        except Exception as e:
            print('下载失败 ', str(e))

    def download_video_start(self):
        """
        调度  开始下载全部都视频
        :return:
        """
        success = []
        err_info = []
        with open('新片场_info.json',mode='r',encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                video_dl_url = data['video_dl_url']

                res = self.video_dl(video_dl_url)
                if not res:
                    err_info.append(data)

        # 设置失败重试  重试三次
        for i in range(3):
            for _ in range(len(err_info)):
                info = err_info.pop()
                video_dl_url = info['video_dl_url']

                res = self.video_dl(video_dl_url)
                if not res:
                    err_info.append(data)



if __name__ == '__main__':
    api = xinpianchang()

    api.get_video_info_start()
    # api.download_video_start()



