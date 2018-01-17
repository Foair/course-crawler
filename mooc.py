#!/usr/bin/python
# -*- coding: utf-8 -*-

""" MOOC 课程下载 """

import os
import sys
import re
import json
import argparse


def cookie_to_json():

    cookies = {}
    raw_cookies = input('> ')

    for cookie in raw_cookies.split(';'):
        key, value = cookie.lstrip().split("=", 1)
        cookies[key] = value

    return cookies


def main():
    parser = argparse.ArgumentParser(description='下载 MOOC 课程。')
    parser.add_argument('url', help='课程地址')
    parser.add_argument('-d', default=r'', help='下载目录')
    parser.add_argument('--no-pdf', action='store_true', help='不下载 PDF 文档')

    args = parser.parse_args()
    if re.match(r'https://www.icourse163.org/course/.+?', args.url):
        # 中国大学MOOC
        import icourse
        icourse.start(args.url, args.d, not args.no_pdf)
    elif re.match(r'http://www.xuetangx.com/courses/.+/about.*', args.url):
        # 学堂在线
        import xuetangx
        if not os.path.isfile('cookies_xuetangx.json'):
            print("输入 cookies 来创建文件：")
            cookies = cookie_to_json()
            with open('cookies_xuetangx.json', 'w') as f:
                json.dump(cookies, f)
        with open('cookies_xuetangx.json') as cookies_file:
            cookies = json.load(cookies_file)
        xuetangx.start(args.url, args.d, not args.no_pdf, cookies)
    elif re.match(r'http://mooc.study.163.com/course/.+?', args.url):
        # 网易云课堂 MOOC
        import study_mooc
        if not os.path.isfile('cookies_mooc_study.json'):
            print("输入 cookies 来创建文件：")
            cookies = cookie_to_json()
            with open('cookies_mooc_study.json', 'w') as f:
                json.dump(cookies, f)
        with open('cookies_mooc_study.json') as cookies_file:
            cookies = json.load(cookies_file)
        study_mooc.start(args.url, args.d, not args.no_pdf, cookies)
    else:
        print('输入地址有误！')
        sys.exit(1)


if __name__ == '__main__':
    main()
