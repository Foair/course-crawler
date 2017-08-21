#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" 「中国大学MOOC」爬虫

一个用于爬取「中国大学MOOC」课程资源的爬虫。

"""
import os
import re
import requests

HEADER = {'User-Agent': 'Mozilla/5.0'}
REG_FILE = re.compile(r'[\\/:\*\?"<>\|]')


def user_input(url):
    """ Return latest course_id and dir name """
    course_page_url = url
    course_page = requests.get(course_page_url, headers=HEADER)
    course_id_number = (re.search(r'termId : "(\d+)"', course_page.text)
                        or re.search(r'id:(\d+)', course_page.text)).group(1)
    names = re.findall(r'name:"(.+)"', course_page.text)
    name = names[0]
    university_name = names[1]
    return course_id_number, name + '——' + university_name


def start(url, path='', pdf=0):
    """ Start crawling """
    global BASE_DIR, RENAMER, VIDEOS, OUTLINE, NEED_PDF
    # Get course basic information
    course_info = user_input(url)

    # Set basic directory
    BASE_DIR = os.path.join(path, REG_FILE.sub('', course_info[1]))

    # Make a directory for new course
    if not os.path.exists(BASE_DIR):
        os.mkdir(BASE_DIR)

    # Whether donwload PDF documnets
    NEED_PDF = pdf

    # Open some global files and wait for writing
    RENAMER = open(os.path.join(
        BASE_DIR, 'Rename.bat'), 'w', encoding='utf-8')
    RENAMER.writelines('chcp 65001\n')
    VIDEOS = open(os.path.join(
        BASE_DIR, 'Videos.txt'), 'w', encoding='utf-8')
    OUTLINE = open(os.path.join(
        BASE_DIR, 'Outline.txt'), 'w', encoding='utf-8')

    # Start crawling
    parse_info(course_info[0])

    # Close files
    RENAMER.close()
    VIDEOS.close()
    OUTLINE.close()


def parse_info(course):
    """ Parse course by termId """
    # Data to post
    postdata = {
        'callCount': '1',
        'scriptSessionId': '${scriptSessionId}190',
        'c0-scriptName': 'CourseBean',
        'c0-methodName': 'getMocTermDto',
        'c0-id': '0',
        'c0-param0': 'number:' + course,
        'c0-param1': 'number:1',
        'c0-param2': 'boolean:true',
        'batchId': '1492167717772'
    }
    info = 'http://www.icourse163.org/dwr/call/plaincall/CourseBean.getMocTermDto.dwr'
    rplsort = re.compile(r'^[第一二三四五六七八九十\d]+[\s\d\._\-章课节讲]*[\.\s、\-]\s*\d*')
    # Get course content
    info = requests.post(info, headers=HEADER,
                         data=postdata).text.encode('utf-8').decode('unicode_escape')
    # print('>>>', info)
    # 查找第 N 周的信息，并返回 [id, name]
    chaps = re.findall(r'homeworks=\w+;.+id=(\d+).+name="(.+)";', info)
    for chapcnt, chap in enumerate(chaps):
        print(chap[1])
        OUTLINE.write('%s {%d}\n' % (chap[1], chapcnt + 1))
        # 查找更小的结构，并返回 [id, name]
        secs = re.findall(
            r'chapterId=' + chaps[chapcnt][0] + r'.+contentType=1.+id=(\d+).+name="(.+)".+test', info)
        for seccnt, sec in enumerate(secs):
            print('  ' + sec[1])
            OUTLINE.write('  %s {%d.%d}\n' % (sec[1], chapcnt + 1, seccnt + 1))

            # 查找视频，并返回 [contentid,contenttype,id,name]
            lessons = re.findall(r'contentId=(\d+).+contentType=(1).+id=(\d+).+lessonId=' +
                                 secs[seccnt][0] + r'.+name="(.+)"', info)
            for lsncnt, lsn in enumerate(lessons):
                OUTLINE.write('    %s {%d.%d.%d}\n' % (
                    lsn[3], chapcnt + 1, seccnt + 1, lsncnt + 1))
                print('    ' + lsn[3])
                name = rplsort.sub('', lsn[3])
                get_content(lessons[lsncnt], '%d.%d.%d %s' %
                            (chapcnt + 1, seccnt + 1, lsncnt + 1, name))

            # 查找文档，并返回 [contentid,contenttype,id,name]
            pdfs = re.findall(r'contentId=(\d+).+contentType=(3).+id=(\d+).+lessonId=' +
                              secs[seccnt][0] + r'.+name="(.+)"', info)
            for pdfcnt, pdf in enumerate(pdfs):
                OUTLINE.write('    %s {%d.%d.%d}*\n' %
                              (pdf[3], chapcnt + 1, seccnt + 1, pdfcnt + 1))
                print('    【课件】' + pdf[3])
                name = rplsort.sub('', pdf[3])
                get_content(pdfs[pdfcnt], '%d.%d.%d %s' %
                            (chapcnt + 1, seccnt + 1, pdfcnt + 1, name))

            richtext = re.findall(r'contentId=(\d+).+contentType=(4).+id=(\d+).+jsonContent="(.+)"}".+lessonId=' +
                                  secs[seccnt][0] + r'.+name="(.+)"', info)
            for textcnt, text in enumerate(richtext):
                # BUG: richtext can contian both HTML and attachment
                OUTLINE.write('    %s {%d.%d.%d}+\n' %
                              (text[4], chapcnt + 1, seccnt + 1, textcnt + 1))
                print('    【富文本】' + text[4])
                name = rplsort.sub('', text[4])
                get_content(richtext[textcnt], '%d.%d.%d %s' %
                            (chapcnt + 1, seccnt + 1, textcnt + 1, name))
                if not text[3] == 'null':
                    print('     【附件】' + text[4])
                    params = {
                        'nosKey': re.search('nosKey":"(.+?)"', text[3]).group(1),
                        'fileName': re.search('"fileName":"(.*)', text[3]).group(1)
                    }
                    filename = REG_FILE.sub(
                        ' ', rplsort.sub('', params['fileName']))
                    OUTLINE.write('    %s %s {%d.%d.%d}!\n' %
                                  (text[4], filename, chapcnt + 1, seccnt + 1, textcnt + 1))
                    if not os.path.isdir(os.path.join(BASE_DIR, 'Files')):
                        os.mkdir(os.path.join(BASE_DIR, 'Files'))
                    attach = requests.get(
                        'http://www.icourse163.org/course/attachment.htm', params=params, headers=HEADER)
                    filename = '%d.%d.%d %s' % (
                        chapcnt + 1, seccnt + 1, textcnt + 1, filename)
                    with open(os.path.join(BASE_DIR, 'Files', filename), 'wb') as file:
                        file.write(attach.content)


def get_content(lesson, name):
    """ Get resource link and download """
    filename = REG_FILE.sub(' ', name)
    postdata = {
        'callCount': '1',
        'scriptSessionId': '${scriptSessionId}190',
        'httpSessionId': '5531d06316b34b9486a6891710115ebc',
        'c0-scriptName': 'CourseBean',
        'c0-methodName': 'getLessonUnitLearnVo',
        'c0-id': '0',
        'c0-param0': 'number:' + lesson[0],
        'c0-param1': 'number:' + lesson[1],
        'c0-param2': 'number:0',
        'c0-param3': 'number:' + lesson[2],
        'batchId': '1492168138043'
    }
    res = 'http://www.icourse163.org/dwr/call/plaincall/CourseBean.getLessonUnitLearnVo.dwr'
    resource = requests.post(res, headers=HEADER, data=postdata).text
    if lesson[1] == '1':
        # mp4url = re.search(r'mp4ShdUrl="(.*?)"', resource).group(1)
        mp4url = (re.search(r'mp4ShdUrl="(.*?\.mp4).*?"', resource) or re.search(r'mp4HdUrl="(.*?\.mp4).*?"',
                                                                                resource) or re.search(r'mp4SdUrl="(.*?\.mp4).*?"', resource)).group(1)
        subtitles = re.findall(r'name="(.+)";.*url="(.*?)"', resource)
        for subtitle in subtitles:
            if len(subtitles) == 1:
                sub_name = filename + '.txt'
            else:
                sub_name = filename + '_' + subtitle[0] + '.txt'
            zimu = requests.get(subtitle[1], headers=HEADER)
            with open(os.path.join(BASE_DIR, sub_name), 'wb') as file:
                file.write(zimu.content)
        print('------->' + name + '.mp4')
        RENAMER.writelines('rename "' + re.search(r'(\w+\.mp4)', mp4url).group(1)
                           + '" "' + filename + '.mp4"' + '\n')
        VIDEOS.writelines(mp4url + '\n')
    elif lesson[1] == '3':
        if os.path.exists(os.path.join(BASE_DIR, 'PDFs', filename + '.pdf')):
            print("------->文件已经存在！")
            return
        pdfurl = re.search(r'textOrigUrl:"(.*?)"', resource).group(1)
        print('------->' + name + '.pdf')
        if NEED_PDF:
            pdf = requests.get(pdfurl, headers=HEADER)
            if not os.path.isdir(os.path.join(BASE_DIR, 'PDFs')):
                os.mkdir(os.path.join(BASE_DIR, 'PDFs'))
            with open(os.path.join(BASE_DIR, 'PDFs', filename + '.pdf'), 'wb') as file:
                file.write(pdf.content)
    elif lesson[1] == '4':
        if os.path.exists(os.path.join(BASE_DIR, 'Texts', filename + '.html')):
            print("------->文件已经存在！")
            return
        text = re.search(r'htmlContent:"(.*)",id',
                         resource.encode('utf-8').decode('unicode_escape'), re.S).group(1)
        print('------->' + name + '.html')
        if not os.path.isdir(os.path.join(BASE_DIR, 'Texts')):
            os.mkdir(os.path.join(BASE_DIR, 'Texts'))
        with open(os.path.join(BASE_DIR, 'Texts', filename + '.html'), 'w', encoding='utf-8') as file:
            file.write(text)

if __name__ == '__main__':
    start('http://www.icourse163.org/course/HEBTU-126003', 'F:\\MOOCs\\', 1)
