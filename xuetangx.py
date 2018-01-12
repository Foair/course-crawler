#!/usr/bin/python
# -*- coding: utf-8 -*-
""" 学堂在线课程下载 """

import re
import os
import sys
import json
import requests
from bs4 import BeautifulSoup

# 基本 URL
BASE_URL = 'http://www.xuetangx.com'

# 定义一个全局的会话
CONNECTION = requests.Session()
CONNECTION.headers.update({'User-Agent': 'Mozilla/5.0'})

# 连续两个以上的空白字符正则表达式
REG_SPACES = re.compile(r'\s+')
# Windows 文件名非法字符的正则表达式
REG_FILE = re.compile(r'[\\/:\*\?"<>\|]')


def get_book(url):
    """ 获得所有的 PDF 电子书 """
    # 含有导航条的页面
    print('正在获取电子书……')
    nav_page = CONNECTION.get(url).text
    shelves = set(re.findall(r'/courses/.+/pdfbook/\d/', nav_page))
    for shelf_count, shelf in enumerate(shelves, 1):
        res = CONNECTION.get(BASE_URL + shelf).text
        soup = BeautifulSoup(res, 'lxml')
        save_dir = os.path.join(BASE_DIR, 'Books', str(shelf_count))
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        for book_count, book in enumerate(soup.select('#booknav a'), 1):
            print('------>', book.string)
            file_name = REG_FILE.sub(' ', book.string) + '.pdf'
            pdf = CONNECTION.get(BASE_URL + book['rel'][0]).content
            with open(os.path.join(save_dir, file_name), 'wb') as pdf_file:
                pdf_file.write(pdf)


def get_handout(url):
    """ 从课程信息页面获得课程讲义的 HTML 文件 """
    res = CONNECTION.get(url).text
    soup = BeautifulSoup(res, 'lxml')
    handouts = soup.find(class_='handouts')
    for link in handouts.select('a[href^="/"]'):
        link['href'] = BASE_URL + link['href']

    with open(os.path.join(BASE_DIR, 'Handouts.html'), 'w', encoding='utf-8') as handouts_html:
        handouts_html.write('<!DOCTYPE html>\n<html>\n<head>\n<title>讲义</title>\n<meta charset="utf-8">\n</head>\n<body>\n%s</body>\n</html>\n' % handouts.prettify())


def get_video(video_id, file_name):
    """ 根据视频 ID 和文件名字获取视频信息 """
    res = CONNECTION.get('https://xuetangx.com/videoid2source/' + video_id).text
    try:
        video_url = json.loads(res)['sources']['quality20'][0]
    except:
        video_url = json.loads(res)['sources']['quality10'][0]
    VIDEOS.write(video_url + '\n')
    RENAMER.write('REN "' + re.search(r'(\w+-[12]0.mp4)', video_url).group(1) + '" "%s.mp4"\n' % file_name)


def get_content(url):
    """ 获取网页详细内容 """
    # 获取课件页面（点击进入学习后的页面）
    courseware = CONNECTION.get(url).text
    soup = BeautifulSoup(courseware, 'lxml')
    # 获取所有章的 DOM 节点
    chapters = soup.find(id='accordion').find_all(class_='chapter')

    for chapter_count, chapter in enumerate(chapters, 1):
        # 章的标题
        chapter_title = chapter.h3.a.get_text(strip=True)

        print('%s' % chapter_title)
        OUTLINE.write('%s {%d}\n' % (chapter_title, chapter_count))

        # 获取节的信息，包括 URL 等
        sections = chapter.select('ul a')
        for section_count, section_info in enumerate(sections, 1):
            # 节的地址
            section_url = BASE_URL + section_info['href']
            # 节的标题
            section_title = section_info.p.string.strip()

            print('  %s' % section_title)
            OUTLINE.write('  %s {%d.%d}\n' % (section_title, chapter_count, section_count))

            # 每个节的页面
            section_page = CONNECTION.get(section_url).text
            soup = BeautifulSoup(section_page, 'lxml')
            tabs = soup.find(id='sequence-list').find_all('li')

            # 视频的编号每一节从 0 开始
            video_sec_count = 0

            for tab_count, tab_info in enumerate(tabs, 1):
                # 每一个 tab（标签）的标题
                # title 可能出现换行符和重复，所以用 data-page-title
                tab_title = tab_info.a.get('data-page-title')

                print('    %s' % tab_title)
                OUTLINE.write('    %s {%d.%d.%d}\n' % (tab_title, chapter_count, section_count, tab_count))

                # 获取 tab 的序列号
                tab_sequence = tab_info.a.get('aria-controls')

                # 获取经过编码后的 tab 内容
                tab_escape = soup.find(id=tab_sequence).string

                tab = BeautifulSoup(tab_escape, 'lxml').div.div

                # tab 中的块
                blocks = tab.find_all('div', class_='xblock')
                for block in blocks:
                    try:
                        # 极少数没有 data-type 属性
                        block_type = block['data-type']
                    except:
                        continue
                    if block_type == 'Problem' or block_type == 'InlineDiscussion' or block_type == 'HTMLModule':
                        continue
                    if block_type == 'Video':
                        video_sec_count += 1
                        # 替换连续空格或制表符为单个空格
                        video_name = REG_SPACES.sub(' ', block.h2.string.strip())
                        OUTLINE.write('      %s {%d.%d.%d}*\n' % (video_name, chapter_count, section_count, video_sec_count))
                        video_id = block.div['data-ccsource']

                        # 文件名
                        file_name = REG_FILE.sub(' ', video_name)
                        file_name = '%d.%d.%d %s' % (chapter_count, section_count, video_sec_count, file_name)

                        print('------>', file_name)
                        get_video(video_id, file_name)

                        # 可用的字幕
                        subtitle_available_url = BASE_URL + block.div['data-transcript-available-translations-url']
                        subtitle_connection = CONNECTION.get(subtitle_available_url)
                        # 为了防止有些课程的章节不提供字幕下载
                        if subtitle_connection.status_code == 200:
                            subtitle_available = subtitle_connection.json()
                            base_subtitle_url = BASE_URL + block.div['data-transcript-translation-url'] + '/'
                            if len(subtitle_available) == 1:
                                multi_subtitle = False
                            else:
                                multi_subtitle = True
                            for subtitle_url in subtitle_available:
                                if multi_subtitle:
                                    sub_file_name = file_name + '_' + subtitle_url + '.str'
                                else:
                                    sub_file_name = file_name + '.str'
                                subtitle_url = base_subtitle_url + subtitle_url
                                CONNECTION.get(subtitle_url)
                                subtitle = CONNECTION.get(subtitle_available_url.rstrip('available_translations') + 'download').content
                                with open(os.path.join(BASE_DIR, sub_file_name), 'wb') as subtitle_file:
                                    subtitle_file.write(subtitle)
                        else:
                            print(file_name+"下载失败")


def start(url, path='', book=True, cookies={}):
    """ 流程控制 """

    global BASE_DIR, VIDEOS, RENAMER, OUTLINE
    requests.utils.add_dict_to_cookiejar(CONNECTION.cookies, cookies)
    status = CONNECTION.get('http://www.xuetangx.com/header_ajax')
    if status.json()['login']:
        print('验证成功！\n')
    else:
        print('Cookies 失效，请获取新的 cookies！')
        sys.exit(1)

    # 课程信息页面
    about_page = CONNECTION.get(url).text
    soup = BeautifulSoup(about_page, 'lxml')

    # 获取课程的标题
    course_name = soup.find(id='title1').string
    # 获取课程的发布者（一般是大学）
    institution = soup.find(class_='courseabout_text').a.string

    # 可以用于文件夹名字的标题
    dir_name = REG_FILE.sub('', course_name + ' - ' + institution)
    print(dir_name)

    BASE_DIR = os.path.join(path, dir_name)

    # 尝试创建文件夹
    try:
        os.makedirs(BASE_DIR)
    except FileExistsError:
        pass

    # 课件页面地址
    courseware = url.rstrip('about') + 'courseware'
    # 课程讲义地址
    handout = url.rstrip('about') + 'info'

    OUTLINE = open(os.path.join(BASE_DIR, 'Outline.txt'), 'w', encoding='utf-8')
    VIDEOS = open(os.path.join(BASE_DIR, 'Videos.txt'), 'w', encoding='utf-8')
    RENAMER = open(os.path.join(BASE_DIR, 'Rename.bat'), 'w', encoding='utf-8')
    RENAMER.write('CHCP 65001\n\n')

    if book:
        # 使用 handout 作为入口更快
        get_book(handout)

    get_handout(handout)
    get_content(courseware)

    VIDEOS.close()
    RENAMER.close()
    OUTLINE.close()


if __name__ == '__main__':
    # start('http://www.xuetangx.com/courses/course-v1:TsinghuaX+00740043X_2015_T2+sp/about', r'F:\MOOCs', True)
    pass
