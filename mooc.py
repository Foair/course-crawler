# -*- coding: utf-8 -*-
"""MOOC 课程下载"""

import os
import sys
import re
import json
import argparse


def store_cookies(file_name):
    """存储并返回 Cookie 字典"""

    def cookie_to_json():
        """将分号分隔的 Cookie 转为字典"""

        cookies_dict = {}
        raw_cookies = input('> ')

        for cookie in raw_cookies.split(';'):
            key, value = cookie.lstrip().split("=", 1)
            cookies_dict[key] = value

        return cookies_dict

    file_name = os.path.join(sys.path[0], file_name)
    if not os.path.isfile(file_name):
        print("输入 Cookie：")
        cookies = cookie_to_json()
        with open(file_name, 'w') as f:
            json.dump(cookies, f)

    with open(file_name) as cookies_file:
        cookies = json.load(cookies_file)

    return cookies


def main():
    """解析命令行参数并调用相关模块进行下载"""

    parser = argparse.ArgumentParser(description='Course Crawler')
    parser.add_argument('url', help='课程地址')
    parser.add_argument('-c', action='store_true', help='执行任务的时候重新输入 cookies（待完成）')
    parser.add_argument('-d', default=r'', help='下载目录')
    parser.add_argument('-r', default='shd', help='视频清晰度')
    parser.add_argument('--inter', action='store_true', help='交互式修改文件名')
    parser.add_argument('--no-doc', action='store_false', help='不下载 PDF、Word 等文档')
    parser.add_argument('--no-sub', action='store_false', help='不下载字幕')
    parser.add_argument('--no-file', action='store_false', help='不下载附件')
    parser.add_argument('--no-text', action='store_false', help='不下载富文本')
    parser.add_argument('--no-dpl', action='store_false', help='不生成播放列表')

    args = parser.parse_args()
    resolutions = ['shd', 'hd', 'sd']

    config = {'doc': args.no_doc, 'sub': args.no_sub, 'file': args.no_file, 'text': args.no_text, 'dpl': args.no_dpl,
              'cookies': args.c, 'rename': args.inter, 'dir': args.d, 'resolution': resolutions.index(args.r.lower())}

    if re.match(r'https?://www.icourse163.org/course/', args.url):
        from mooc import icourse163
        icourse163.start(args.url, config)
    elif re.match(r'https?://www.xuetangx.com/courses/.+/about', args.url):
        from mooc import xuetangx
        cookies = store_cookies('xuetangx.json')
        xuetangx.start(args.url, config, cookies)
    elif re.match(r'https?://mooc.study.163.com/course/', args.url):
        from mooc import study_mooc
        cookies = store_cookies('study_163_mooc.json')
        study_mooc.start(args.url, config, cookies)
    elif re.match(r'https?://www.cnmooc.org/portal/course/', args.url):
        from mooc import cnmooc
        cookies = store_cookies('cnmooc.json')
        cnmooc.start(args.url, config, cookies)
    elif re.match(r'https?://www.icourses.cn/web/sword/portal/videoDetail', args.url):
        from mooc import icourses
        icourses.start(args.url, config)
    else:
        print('课程地址有误！')
        sys.exit(1)


if __name__ == '__main__':
    main()
