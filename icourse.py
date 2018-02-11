#!/usr/bin/python
# -*- coding: utf-8 -*-
""" 中国大学MOOC 课程下载 """

import re
import time
from utils import *

CANDDY = Crawler()

def get_summary(url):
    """ 从课程主页面获取信息 """
    res = CANDDY.get(url).text

    # 当前学期编号
    term_id = re.search(r'termId : "(\d+)"', res).group(1)
    names = re.findall(r'name:"(.+)"', res)

    dir_name = CourseDir(names[0], names[1])

    print(dir_name)
    return term_id, dir_name


def get_resource(term_id):
    """ 获取各种资源 """

    outline = Outline()
    playlist = Playlist()
    videos_list = []
    pdf_list = []
    rich_text_list = []
    attach_list = []

    post_data = {'callCount': '1', 'scriptSessionId': '${scriptSessionId}190', 'c0-scriptName': 'CourseBean', 'c0-methodName': 'getMocTermDto', 'c0-id': '0', 'c0-param0': 'number:' + term_id, 'c0-param1': 'number:1', 'c0-param2': 'boolean:true', 'batchId': str(int(time.time() * 1000))}
    res = CANDDY.post('https://www.icourse163.org/dwr/call/plaincall/CourseBean.getMocTermDto.dwr', data=post_data).text.encode('utf-8').decode('unicode_escape')

    # 查找第 N 周的开课信息（正则匹配到 [id, name]）
    chapters = re.findall(r'homeworks=\w+;.+id=(\d+).+name="(.+)";', res)
    for chapter_count, chapter in enumerate(chapters, start=1):
        outline.write(chapter[1], 0, chapter_count)

        # 每节的信息
        lessons = re.findall(r'chapterId=' + chapters[chapter_count - 1][0] + r'.+contentType=1.+id=(\d+).+name="(.+)".+test', res)
        for lesson_count, lesson in enumerate(lessons, start=1):
            outline.write(lesson[1], 1, chapter_count, lesson_count)

            # 视频（正则匹配到 [contentId, contentType, id, name]）
            videos = re.findall(r'contentId=(\d+).+contentType=(1).+id=(\d+).+lessonId=' + lessons[lesson_count - 1][0] + r'.+name="(.+)"', res)
            for video_count, video in enumerate(videos, start=1):
                outline.write(video[3], 2, chapter_count, lesson_count, video_count, sign='#')
                videos_list.append(Video(chapter_count, lesson_count, video_count, video[3], videos[video_count - 1]))

            # 课件（正则匹配到 [contentId, contentType, id, name]）
            pdfs = re.findall(r'contentId=(\d+).+contentType=(3).+id=(\d+).+lessonId=' + lessons[lesson_count - 1][0] + r'.+name="(.+)"', res)
            for pdf_count, pdf in enumerate(pdfs, start=1):
                outline.write(pdf[3], 2, chapter_count, lesson_count, pdf_count, sign='*')
                if CONFIG['pdf']:
                    pdf_list.append(Document(chapter_count, lesson_count, pdf_count, pdf[3], pdfs[pdf_count - 1]))

            # 富文本（正则匹配到 [contentId, contentType, id, jsonContent, name]）
            rich_text = re.findall(r'contentId=(\d+).+contentType=(4).+id=(\d+).+jsonContent=(.+);.+lessonId=' + lessons[lesson_count - 1][0] + r'.+name="(.+)"', res)
            for text_count, text in enumerate(rich_text, start=1):
                outline.write(text[4], 2, chapter_count, lesson_count, text_count, sign='+')
                rich_text_list.append(RichText(chapter_count, lesson_count, text_count, text[4], rich_text[text_count - 1]))

                if text[3] != 'null' and text[3] != '""':
                    params = {'nosKey': re.search('nosKey":"(.+?)"', text[3]).group(1), 'fileName': re.search('"fileName":"(.+?)"', text[3]).group(1)}
                    file_name = Resource.regex_file.sub('', rplsort.sub('', params['fileName']))
                    outline.write(file_name, 2, chapter_count, lesson_count, text_count, sign='!')

                    WORK_DIR.change('Files')
                    print('------>', params['fileName'])
                    file_name = '%d.%d.%d %s' % (chapter_count, lesson_count, text_count, file_name)
                    attach = CANDDY.download_bin('https://www.icourse163.org/course/attachment.htm', WORK_DIR.file(file_name), params=params)

    WORK_DIR.change('Videos')
    parse_res_list(videos_list, WORK_DIR.file('Video_names.txt'), playlist, parse_resource)
    WORK_DIR.change('PDFs')
    parse_res_list(pdf_list, WORK_DIR.file('PDF_names.txt'), parse_resource)
    WORK_DIR.change('Texts')
    parse_res_list(rich_text_list, None, parse_resource)


def parse_resource(resource):
    """ 解析资源地址和下载资源 """
    file_name = resource.file_name
    # 传入的 resource.meta 只会用到前 3 个参数（contentId、contentType 和 id）
    # 3 个参数都会传给服务器
    # 第 1 个用来判断资源类型，因为不同的资源有不同的正则匹配方法

    post_data = {'callCount': '1', 'scriptSessionId': '${scriptSessionId}190', 'httpSessionId': '5531d06316b34b9486a6891710115ebc', 'c0-scriptName': 'CourseBean', 'c0-methodName': 'getLessonUnitLearnVo', 'c0-id': '0', 'c0-param0': 'number:' + resource.meta[0], 'c0-param1': 'number:' + resource.meta[1], 'c0-param2': 'number:0', 'c0-param3': 'number:' + resource.meta[2], 'batchId': str(int(time.time() * 1000))}
    res = CANDDY.post('https://www.icourse163.org/dwr/call/plaincall/CourseBean.getLessonUnitLearnVo.dwr', data=post_data).text

    # meta[1] 的有：1（视频），3（PDF 文档），4（富文本）
    if resource.type == 'Video':
        mp4url = (re.search(r'mp4ShdUrl="(.*?\.mp4.*?)"', res) or re.search(r'mp4HdUrl="(.*?\.mp4.*?)"', res) or re.search(r'mp4SdUrl="(.*?\.mp4.*?)"', res)).group(1)
        # 查找字幕
        subtitles = re.findall(r'name="(.+)";.*url="(.*?)"', res)
        for subtitle in subtitles:
            # 如果只有一种语言的字幕
            if len(subtitles) == 1:
                sub_name = file_name + '.srt'
            else:
                # <字幕名称>_<语言>.srt
                subtitle_lang = subtitle[0].encode('utf-8').decode('unicode_escape')
                sub_name = file_name + '_' + subtitle_lang + '.srt'
            print('------>', sub_name)
            CANDDY.download_bin(subtitle[1], WORK_DIR.file('Videos', sub_name))
        print('------>', file_name + '.mp4')
        RENAMER.write(re.search(r'(\w+\.mp4)', mp4url).group(1), file_name)
        VIDEOS.write(mp4url)

    elif resource.type == 'Documents':
        if WORK_DIR.exist(file_name + '.pdf'):
            return
        pdf_url = re.search(r'textOrigUrl:"(.*?)"', res).group(1)
        print('------>', file_name + '.pdf')
        CANDDY.download_bin(pdf_url, WORK_DIR.file(file_name + '.pdf'))

    elif resource.type == 'Rich texts':
        if WORK_DIR.exist(file_name + '.html'):
            return
        text = re.search(r'htmlContent:"(.*)",id', res.encode('utf-8').decode('unicode_escape'), re.S).group(1)
        print('------>', file_name + '.html')
        with open(WORK_DIR.file(file_name + '.html'), 'w', encoding='utf-8') as file:
            file.write(text)


def start(url, path='', pdf=True):
    """ 流程控制 """

    global CONFIG, WORK_DIR, RENAMER, VIDEOS

    # 获取课程信息
    course_info = get_summary(url)

    # 设置根目录
    WORK_DIR = WorkingDir(path, course_info[1])

    RENAMER = Renamer('Rename.bat')
    VIDEOS = ClassicFile('Videos.txt')

    # 是否需要 PDF 课件
    CONFIG = {}
    CONFIG['pdf'] = pdf

    # course_info[0] 就是 termId
    get_resource(course_info[0])


if __name__ == '__main__':
    # start('https://www.icourse163.org/course/NEU-1001956020', '', False)
    start('https://www.icourse163.org/course/CSU-1002475002', '', True)
    # start('https://www.icourse163.org/course/WHU-1002480002', '', True)
    pass
