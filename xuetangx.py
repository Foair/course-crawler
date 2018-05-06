# -*- coding: utf-8 -*-
"""学堂在线 课程下载"""

import re
import json
from bs4 import BeautifulSoup
from utils import *

BASE_URL = 'http://www.xuetangx.com'
CNADY = Crawler()


def get_book(url):
    """获得所有的 PDF 电子书"""
    nav_page = CNADY.get(url).text
    shelves = set(re.findall(r'/courses/.+/pdfbook/\d/', nav_page))
    for shelf_count, shelf in enumerate(shelves, 1):
        res = CNADY.get(BASE_URL + shelf).text
        soup = BeautifulSoup(res, 'lxml')
        WORK_DIR.change('Books', str(shelf_count))
        for book_count, book in enumerate(soup.select('#booknav a'), 1):
            src_print(book.string)
            file_name = file_to_save(book.string) + '.pdf'
            pdf = CNADY.get(BASE_URL + book['rel'][0]).content
            with open(WORK_DIR.file(file_name), 'wb') as pdf_file:
                pdf_file.write(pdf)


def get_handout(url):
    """从课程信息页面获得课程讲义的 HTML 文件"""
    res = CNADY.get(url).text
    soup = BeautifulSoup(res, 'lxml')
    handouts = soup.find(class_='handouts')
    for link in handouts.select('a[href^="/"]'):
        link['href'] = BASE_URL + link['href']
    with open('Handouts.html', 'w', encoding='utf-8') as handouts_html:
        handouts_html.write('<!DOCTYPE html>\n<html>\n<head>\n<title>讲义</title>\n<meta charset="utf-8">\n</head>\n<body>\n%s</body>\n</html>\n' % handouts.prettify())


def get_video(video):
    """根据视频 ID 和文件名字获取视频信息"""
    file_name = video.file_name
    src_print(file_name + '.mp4')
    res = CNADY.get('https://xuetangx.com/videoid2source/' + video.meta).text
    try:
        video_url = json.loads(res)['sources']['quality20'][0]
    except:
        video_url = json.loads(res)['sources']['quality10'][0]
    VIDEOS.write(video_url)
    RENAMER.write(re.search(r'(\w+-[12]0.mp4)', video_url).group(1), file_name)


def get_content(url):
    """ 获取网页详细内容 """

    outline = Outline()
    counter = Counter()
    video_counter = Counter()
    playlist = Playlist()
    video_list = []

    courseware = CNADY.get(url).text
    soup = BeautifulSoup(courseware, 'lxml')

    chapters = soup.find(id='accordion').find_all(class_='chapter')
    for chapter in chapters:
        counter.add(0)
        video_counter.add(0)
        chapter_title = chapter.h3.a.get_text(strip=True)
        outline.write(chapter_title, counter, 0)

        sections = chapter.select('ul a')
        for section_info in sections:
            counter.add(1)
            video_counter.add(1)
            section_url = BASE_URL + section_info['href']
            section_title = section_info.p.string.strip()

            outline.write(section_title, counter, 1)

            section_page = CNADY.get(section_url).text
            soup = BeautifulSoup(section_page, 'lxml')

            tabs = soup.find(id='sequence-list').find_all('li')
            for tab_count, tab_info in enumerate(tabs, 1):
                counter.add(2)
                # title 可能出现换行符和重复，所以用 data-page-title
                tab_title = tab_info.a.get('data-page-title')

                outline.write(tab_title, counter)

                if tab_title == 'Video' or tab_title == '视频' or tab_title == '':
                    tab_title = section_title

                tab_sequence = tab_info.a.get('aria-controls')

                tab_escape = soup.find(id=tab_sequence).string
                tab = BeautifulSoup(tab_escape, 'lxml').div.div

                blocks = tab.find_all('div', class_='xblock')
                for block in blocks:
                    try:
                        # 极少数没有 data-type 属性
                        block_type = block['data-type']
                    except:
                        continue
                    if block_type == 'Video':
                        video_counter.add(2)
                        # 替换连续空格或制表符为单个空格
                        video_name = block.h2.string.strip()

                        outline.write(video_name, video_counter, level=3, sign='#')

                        if video_name == 'Video' or video_name == '视频' or video_name == '':
                            video_name = tab_title

                        video_id = block.div['data-ccsource']

                        video = Video(video_counter, video_name, video_id)
                        video_list.append(video)

                        if CONFIG['sub']:
                            get_subtitles(block.div['data-transcript-available-translations-url'], block.div['data-transcript-translation-url'], video.file_name)
    if video_list:
        WORK_DIR.change('Videos')
        parse_res_list(video_list, WORK_DIR.file('Names.txt'), playlist, get_video)
        
def get_subtitles(avaliable, transcript, file_name):
        subtitle_available_url = BASE_URL + avaliable
        try:
            subtitle_available = CNADY.get(subtitle_available_url).json()
        except:
            return
        WORK_DIR.change('Videos')
        base_subtitle_url = BASE_URL + transcript + '/'
        multi_subtitle = False if len(subtitle_available) == 1 else True
        for subtitle_desc in subtitle_available:
            subtitle_url = base_subtitle_url + subtitle_desc
            CNADY.get(subtitle_url)
            if multi_subtitle:
                sub_file_name = file_name + '_' + subtitle_desc.replace('_xuetangx', '') + '.srt'
            else:
                sub_file_name = file_name + '.srt'
            subtitle = CNADY.get(subtitle_available_url.rstrip('available_translations') + 'download').content
            with open(WORK_DIR.file(sub_file_name), 'wb') as subtitle_file:
                subtitle_file.write(subtitle)

def get_summary(url):
    about_page = CNADY.get(url).text
    soup = BeautifulSoup(about_page, 'lxml')

    course_name = soup.find(id='title1').string
    institution = soup.find(class_='courseabout_text').a.string

    dir_name = CourseDir(course_name, institution)
    print(dir_name)
    return dir_name


def start(url, path='', book=True, sub=True, files=True, text=True, cookies={}):
    """调用接口"""

    global VIDEOS, RENAMER, WORK_DIR, CONFIG
    CONFIG = {'book': book, 'sub': sub, 'file': files, 'text': text}

    CNADY.set_cookies(cookies)
    status = CNADY.get('http://www.xuetangx.com/header_ajax')
    if status.json()['login']:
        print('验证成功！')
    else:
        print('Cookies 失效，请获取新的 cookies！')
        return

    course_name = get_summary(url)

    WORK_DIR = WorkingDir(path, course_name)
    WORK_DIR.change('Videos')
    RENAMER = Renamer(WORK_DIR.file('Rename.bat'))
    VIDEOS = ClassicFile(WORK_DIR.file('Videos.txt'))

    handout = url.rstrip('about') + 'info'
    courseware = url.rstrip('about') + 'courseware'

    if CONFIG['book']:
        # 使用 handout 作为入口更快
        get_book(handout)

    get_handout(handout)
    get_content(courseware)



if __name__ == '__main__':
    # start('http://www.xuetangx.com/courses/course-v1:TsinghuaX+00740043X_2015_T2+sp/about', r'F:\MOOCs', True)
    pass
