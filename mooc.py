# -*- coding: utf-8 -*-
"""MOOC 课程下载"""

import os
import sys
import re
import json
import argparse


def store_cookies(fname):
    """存储并返回 cookies 字典"""

    def cookie_to_json():
        """将分号分隔的 cookies 转为字典"""
        cookies = {}
        raw_cookies = input('> ')

        for cookie in raw_cookies.split(';'):
            key, value = cookie.lstrip().split("=", 1)
            cookies[key] = value

        return cookies

    if not os.path.isfile(fname):
        print("输入 cookies 来创建文件：")
        cookies = cookie_to_json()
        with open(fname, 'w') as f:
            json.dump(cookies, f)
    with open(fname) as cookies_file:
        cookies = json.load(cookies_file)

    return cookies


def main():
    """解析命令行参数并调用相关模块进行下载"""
    parser = argparse.ArgumentParser(description='下载 MOOC 课程的程序。')
    parser.add_argument('url', help='课程地址')
    parser.add_argument('-d', default=r'G:\MOOCs', help='下载目录')
    parser.add_argument('-i', action='store_true', help='交互式修改文件名')
    parser.add_argument('--no-pdf', action='store_false', help='不下载 PDF 文档')
    parser.add_argument('--no-sub', action='store_false', help='不下载字幕')
    parser.add_argument('--no-file', action='store_false', help='不下载附件')
    parser.add_argument('--no-text', action='store_false', help='不下载富文本')
    args = parser.parse_args()

    if re.match(r'https?://www.icourse163.org/course/.+?', args.url):
        import icourse
        icourse.start(args.url, args.d, args.no_pdf, args.no_sub, args.no_file, args.no_text)
    elif re.match(r'https?://www.xuetangx.com/courses/.+/about.*', args.url):
        import xuetangx
        cookies = store_cookies('xuetangx.json')
        xuetangx.start(args.url, args.d, args.no_pdf, args.no_sub, args.no_file, args.no_text, cookies)
    elif re.match(r'https?://mooc.study.163.com/course/.+?', args.url):
        import study_mooc
        cookies = store_cookies('study_163_mooc.json')
        study_mooc.start(args.url, args.d, args.no_pdf, cookies)
    else:
        print('输入课程地址有误！')
        sys.exit(1)


if __name__ == '__main__':
    main()
