#!/usr/bin/python
# -*- coding: utf-8 -*-
""" 网易云课堂 MOOC 课程下载 """

import os
import re
import time
import requests

# 创建一个全局的 requests 的会话
CONNECTION = requests.Session()

# 模拟浏览器
HEADER = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36'}
# 更新会话的 user agent
CONNECTION.headers.update(HEADER)

# Windows 文件名非法字符
REG_FILE = re.compile(r'[\\/:\*\?"<>\|]')


def get_summary(url):
    """ 从课程主页面获取信息 """

    res = CONNECTION.get(url).text

    # 最新的学期编号
    term_id = re.search(r'termId : "(\d+)"', res).group(1)

    names = re.findall(r'name:"(.+)"', res)
    # 课程名称
    course_name = names[0]
    # 开课机构
    institution = names[1]

    # 文件夹名称
    dir_name = REG_FILE.sub('', course_name + ' - ' + institution)
    print(dir_name)

    return term_id, dir_name


def get_announce(term_id):
    """ 获取课程的公告 """

    # batchId 的生成方法为 str(int(time.time() * 1000))
    post_data = {'callCount': '1', 'scriptSessionId': '${scriptSessionId}190', 'httpSessionId': 'dba4977be78d42a78a6e2c2dd2b9bb42', 'c0-scriptName': 'CourseBean', 'c0-methodName': 'getAllAnnouncementByTerm', 'c0-id': '0', 'c0-param0': 'number:' + term_id, 'c0-param1': 'number:1', 'batchId': str(int(time.time() * 1000))}
    res = CONNECTION.post('http://mooc.study.163.com/dwr/call/plaincall/CourseBean.getAllAnnouncementByTerm.dwr', data=post_data).text

    announcements = re.findall(r'content="(.*?[^\\])".*title="(.*?[^\\])"', res)

    with open(os.path.join(BASE_DIR, 'Announcements.html'), 'w', encoding='utf-8') as announce_file:
        for announcement in announcements:
            # 公告内容
            announce_content = announcement[0].encode('utf-8').decode('unicode_escape')
            # 公告标题
            announce_title = announcement[1].encode('utf-8').decode('unicode_escape')
            announce_file.write('<h1>' + announce_title + '</h1>\n' + announce_content + '\n')


def get_resource(term_id):
    """ 获取各种资源 """

    # 删除原有的课程排序（replace sort）
    rplsort = re.compile(r'^[第一二三四五六七八九十\d]+[\s\d\._\-章课节讲]*[\.\s、\-]\s*\d*')

    post_data = {'callCount': '1', 'scriptSessionId': '${scriptSessionId}190', 'httpSessionId': 'b8efd4c73fd1434896507b83de631f0f', 'c0-scriptName': 'CourseBean', 'c0-methodName': 'getLastLearnedMocTermDto', 'c0-id': '0', 'c0-param0': 'number:' + term_id, 'batchId': str(int(time.time() * 1000))}
    res = CONNECTION.post('http://mooc.study.163.com/dwr/call/plaincall/CourseBean.getLastLearnedMocTermDto.dwr', data=post_data).text.encode('utf-8').decode('unicode-escape')

    # 查找第 N 周的开课信息（正则匹配到 [id, name]）
    chapters = re.findall(r'homeworks=\w+;.+id=(\d+).+name="(.*?)";', res)
    for chapter_count, chapter in enumerate(chapters, start=1):
        print(chapter[1])
        OUTLINE.write('%s {%d}\n' % (chapter[1], chapter_count))

        # 每节的信息
        lessons = re.findall(r'chapterId=' + chapters[chapter_count - 1][0] + r'.+contentType=1.+id=(\d+).+name="(.*?)".+test', res)
        for lesson_count, lesson in enumerate(lessons, start=1):
            print('  ' + lesson[1])
            OUTLINE.write('  %s {%d.%d}\n' % (lesson[1], chapter_count, lesson_count))

            # 视频（正则匹配到 [contentId, contentType, id, name]）
            videos = re.findall(r'contentId=(\d+).+contentType=(1).+id=(\d+).+lessonId=' + lessons[lesson_count - 1][0] + r'.+name="(.*?)";', res)
            for video_count, video in enumerate(videos, start=1):
                print('    ' + video[3])
                OUTLINE.write('    %s {%d.%d.%d}\n' % (video[3], chapter_count, lesson_count, video_count))

                name = rplsort.sub('', video[3])
                parse_resource(term_id, videos[video_count - 1], '%d.%d.%d %s' % (chapter_count, lesson_count, video_count, name))

            # 课件（正则匹配到 [contentId, contentType, id, name]）
            pdfs = re.findall(r'contentId=(\d+).+contentType=(3).+id=(\d+).+lessonId=' + lessons[lesson_count - 1][0] + r'.+name="(.*?)";', res)
            for pdf_count, pdf in enumerate(pdfs, start=1):
                print('    【课件】' + pdf[3])
                OUTLINE.write('    %s {%d.%d.%d}*\n' % (pdf[3], chapter_count, lesson_count, pdf_count))

                name = rplsort.sub('', pdf[3])
                parse_resource(term_id, pdfs[pdf_count - 1], '%d.%d.%d %s' % (chapter_count, lesson_count, pdf_count, name))

            # 富文本（正则匹配到 [contentId, contentType, id, jsonContent, name]）
            rich_text = re.findall(r'contentId=(\d+).+contentType=(4).+id=(\d+).+jsonContent=(.+);.+lessonId=' + lessons[lesson_count - 1][0] + r'.+name="(.*?[^\\])"', res)
            for text_count, text in enumerate(rich_text, start=1):
                print('    【富文本】' + text[4])
                OUTLINE.write('    %s {%d.%d.%d}+\n' % (text[4], chapter_count, lesson_count, text_count))

                name = rplsort.sub('', text[4])
                parse_resource(term_id, rich_text[text_count - 1], '%d.%d.%d %s' % (chapter_count, lesson_count, text_count, name))

                if text[3] != 'null':
                    print('    【附件】' + text[4])
                    params = {'nosKey': re.search('nosKey":"(.+?)"', text[3]).group(1), 'fileName': re.search('"fileName":"(.*?)"', text[3]).group(1)}
                    file_name = REG_FILE.sub('', rplsort.sub('', params['fileName']))
                    OUTLINE.write('    %s %s {%d.%d.%d}!\n' % (text[4], file_name, chapter_count, lesson_count, text_count))

                    # 直接下载附件
                    if not os.path.isdir(os.path.join(BASE_DIR, 'Files')):
                        os.mkdir(os.path.join(BASE_DIR, 'Files'))
                    print('------>', params['fileName'])
                    attach = CONNECTION.get('http://www.icourse163.org/course/attachment.htm', params=params)
                    file_name = '%d.%d.%d %s' % (chapter_count, lesson_count, text_count, file_name)
                    with open(os.path.join(BASE_DIR, 'Files', file_name), 'wb') as file:
                        file.write(attach.content)


def parse_resource(term_id, res_info, name):
    """ 解析资源地址和下载资源 """

    # 传入的 res_info 只会用到前 3 个参数（contentId、contentType 和 id）
    # 第 0 个和第 2 个用来传给服务器
    # 第 1 个用来判断资源类型，因为不同的资源有不同的正则匹配方法

    # 替换名字中的非法字符用作文件名
    file_name = REG_FILE.sub('', name)

    post_data = {'callCount': '1', 'scriptSessionId': '${scriptSessionId}190', 'httpSessionId': 'b8efd4c73fd1434896507b83de631f0f', 'c0-scriptName': 'CourseBean', 'c0-methodName': 'getLessonUnitLearnVo', 'c0-id': '0', 'c0-param0': 'number:' + term_id, 'c0-param1': 'number:' + res_info[0], 'c0-param2': 'number:' + res_info[1], 'c0-param3': 'number:0', 'c0-param4': 'number:' + res_info[2], 'batchId': str(int(time.time() * 1000))}
    res = CONNECTION.post('http://mooc.study.163.com/dwr/call/plaincall/CourseBean.getLessonUnitLearnVo.dwr', data=post_data).text

    # 视频资源
    if res_info[1] == '1':
        mp4url = (re.search(r'mp4ShdUrl="(.*?\.mp4.*?)"', res) or re.search(r'mp4HdUrl="(.*?\.mp4.*?)"', res) or re.search(r'mp4SdUrl="(.*?\.mp4.*?)"', res)).group(1)
        # 查找字幕
        subtitles = re.findall(r'name="(.+)";.*url="(.*?)"', res)
        for subtitle in subtitles:
            # 如果只有一种语言的字幕
            if len(subtitles) == 1:
                sub_name = file_name + '.srt'
            else:
                # <字幕名称>_<语言>.txt
                sub_name = file_name + '_' + subtitle[0].encode('utf-8').decode('unicode_escape') + '.srt'
            print('------>', sub_name)
            res = requests.get(subtitle[1], headers=HEADER)
            with open(os.path.join(BASE_DIR, sub_name), 'wb') as file:
                file.write(res.content)

        print('------>', name + '.mp4')
        RENAMER.write('REN "' + re.search(r'(\w+\.mp4)', mp4url).group(1) + '" "' + file_name + '.mp4"' + '\n')
        VIDEOS.write(mp4url + '\n')

    # 获取 PDF 文档
    elif res_info[1] == '3':
        if os.path.exists(os.path.join(BASE_DIR, 'PDFs', file_name + '.pdf')):
            print("------> 文件已经存在！")
            return
        pdf_url = re.search(r'textOrigUrl:"(.*?)"', res).group(1)
        print('------>', name + '.pdf')
        if WANT_PDF:
            pdf = requests.get(pdf_url, headers=HEADER)
            if not os.path.isdir(os.path.join(BASE_DIR, 'PDFs')):
                os.mkdir(os.path.join(BASE_DIR, 'PDFs'))
            with open(os.path.join(BASE_DIR, 'PDFs', file_name + '.pdf'), 'wb') as file:
                file.write(pdf.content)

    # 获取富文本
    elif res_info[1] == '4':
        if os.path.exists(os.path.join(BASE_DIR, 'Texts', file_name + '.html')):
            print("------> 文件已经存在！")
            return
        text = re.search(r'htmlContent:"(.*)",id', res.encode('utf-8').decode('unicode_escape'), re.S).group(1)
        print('------>', name + '.html')
        if not os.path.isdir(os.path.join(BASE_DIR, 'Texts')):
            os.mkdir(os.path.join(BASE_DIR, 'Texts'))
        with open(os.path.join(BASE_DIR, 'Texts', file_name + '.html'), 'w', encoding='utf-8') as file:
            file.write(text)


def start(url, path='', pdf=True, cookies={}):
    """ 流程控制 """

    global BASE_DIR, RENAMER, VIDEOS, OUTLINE, WANT_PDF

    # 添加 cookies 到会话的头部中
    requests.utils.add_dict_to_cookiejar(CONNECTION.cookies, cookies)

    # 获取课程信息
    course_info = get_summary(url)

    # 设置根目录
    BASE_DIR = os.path.join(path, REG_FILE.sub('', course_info[1]))

    # 如果不存在课程目录，则创建它
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR)

    # 是否需要 PDF 课件
    WANT_PDF = pdf

    # 打开一些文件方便写入
    VIDEOS = open(os.path.join(BASE_DIR, 'Videos.txt'), 'w', encoding='utf-8')
    OUTLINE = open(os.path.join(BASE_DIR, 'Outline.txt'), 'w', encoding='utf-8')
    RENAMER = open(os.path.join(BASE_DIR, 'Rename.bat'), 'w', encoding='utf-8')
    RENAMER.write('CHCP 65001\n\n')

    # course_info[0] 就是 termId
    get_announce(course_info[0])
    get_resource(course_info[0])

    # 关闭文件
    RENAMER.close()
    VIDEOS.close()
    OUTLINE.close()


if __name__ == '__main__':
    # start('http://mooc.study.163.com/course/1000031001?tid=2001355027#/info', r'F:\MOOCs', True)
    pass
