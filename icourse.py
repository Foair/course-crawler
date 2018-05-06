# -*- coding: utf-8 -*-
"""中国大学MOOC"""

import re
import time
from utils import *

CANDDY = Crawler()


def get_summary(url):
    """从课程主页面获取信息"""
    res = CANDDY.get(url).text

    term_id = re.search(r'termId : "(\d+)"', res).group(1)
    names = re.findall(r'name:"(.+)"', res)

    dir_name = CourseDir(names[0], names[1])

    print(dir_name)
    return term_id, dir_name


def get_resource(term_id):
    """获取各种资源"""

    outline = Outline()
    playlist = Playlist()
    counter = Counter()
    video_list = []
    pdf_list = []
    rich_text_list = []
    # $$$ 删除下面 rplsort
    rplsort = re.compile(r'^[第一二三四五六七八九十\d]+[\s\d\._\-章课节讲]*[\.\s、\-]\s*\d*')
    post_data = {'callCount': '1', 'scriptSessionId': '${scriptSessionId}190', 'c0-scriptName': 'CourseBean', 'c0-methodName': 'getMocTermDto', 'c0-id': '0', 'c0-param0': 'number:' + term_id, 'c0-param1': 'number:0', 'c0-param2': 'boolean:true', 'batchId': str(int(time.time() * 1000))}
    res = CANDDY.post('https://www.icourse163.org/dwr/call/plaincall/CourseBean.getMocTermDto.dwr', data=post_data).text.encode('utf_8').decode('unicode_escape')
    chapters = re.findall(r'homeworks=\w+;.+id=(\d+).+name="(.+)";', res)
    for chapter in chapters:
        counter.add(0)
        outline.write(chapter[1], counter, 0)

        lessons = re.findall(r'chapterId=' + chapter[0] + r'.+contentType=1.+id=(\d+).+name="(.+)".+test', res)
        for lesson in lessons:
            counter.add(1)
            outline.write(lesson[1], counter, 1)

            videos = re.findall(r'contentId=(\d+).+contentType=(1).+id=(\d+).+lessonId=' + lesson[0] + r'.+name="(.+)"', res)
            for video in videos:
                counter.add(2)
                outline.write(video[3], counter, 2, sign='#')
                video_list.append(Video(counter, video[3], video))
            counter.reset()

            pdfs = re.findall(r'contentId=(\d+).+contentType=(3).+id=(\d+).+lessonId=' + lesson[0] + r'.+name="(.+)"', res)
            for pdf in pdfs:
                counter.add(2)
                outline.write(pdf[3], counter, 2, sign='*')
                if CONFIG['pdf']:
                    pdf_list.append(Document(counter, pdf[3], pdf))
            counter.reset()

            rich_text = re.findall(r'contentId=(\d+).+contentType=(4).+id=(\d+).+jsonContent=(.+);.+lessonId=' + lesson[0] + r'.+name="(.+)"', res)
            for text in rich_text:
                counter.add(2)
                outline.write(text[4], counter, 2, sign='+')
                if CONFIG['text']:
                    rich_text_list.append(RichText(counter, text[4], text))
                if CONFIG['file']:
                    if text[3] != 'null' and text[3] != '""':
                        params = {'nosKey': re.search('nosKey":"(.+?)"', text[3]).group(1), 'fileName': re.search('"fileName":"(.+?)"', text[3]).group(1)}
                        file_name = Resource.regex_file.sub('', rplsort.sub('', params['fileName']))
                        outline.write(file_name, counter, 2, sign='!')

                        WORK_DIR.change('Files')
                        src_print(params['fileName'])
                        file_name = '%s %s' % (counter, file_name)
                        CANDDY.download_bin('https://www.icourse163.org/course/attachment.htm', WORK_DIR.file(file_name), params=params)
            counter.reset()

    if video_list:
        WORK_DIR.change('Videos')
        parse_res_list(video_list, WORK_DIR.file('Names.txt'), playlist, parse_resource)
    if pdf_list:
        WORK_DIR.change('PDFs')
        parse_res_list(pdf_list, WORK_DIR.file('Names.txt'), parse_resource)
    if rich_text_list:
        WORK_DIR.change('Texts')
        parse_res_list(rich_text_list, None, parse_resource)


def parse_resource(resource):
    """解析资源地址和下载资源"""
    file_name = resource.file_name

    post_data = {'callCount': '1', 'scriptSessionId': '${scriptSessionId}190', 'httpSessionId': '5531d06316b34b9486a6891710115ebc', 'c0-scriptName': 'CourseBean', 'c0-methodName': 'getLessonUnitLearnVo', 'c0-id': '0', 'c0-param0': 'number:' + resource.meta[0], 'c0-param1': 'number:' + resource.meta[1], 'c0-param2': 'number:0', 'c0-param3': 'number:' + resource.meta[2], 'batchId': str(int(time.time() * 1000))}
    res = CANDDY.post('https://www.icourse163.org/dwr/call/plaincall/CourseBean.getLessonUnitLearnVo.dwr', data=post_data).text

    if resource.type == 'Video':
        mp4url = (re.search(r'mp4ShdUrl="(.*?\.mp4.*?)"', res) or re.search(r'mp4HdUrl="(.*?\.mp4.*?)"', res) or re.search(r'mp4SdUrl="(.*?\.mp4.*?)"', res)).group(1)
        src_print(file_name + '.mp4')
        RENAMER.write(re.search(r'(\w+\.mp4)', mp4url).group(1), file_name)
        VIDEOS.write(mp4url)

        if not CONFIG['sub']: return
        subtitles = re.findall(r'name="(.+)";.*url="(.*?)"', res)
        for subtitle in subtitles:
            if len(subtitles) == 1:
                sub_name = file_name + '.srt'
            else:
                subtitle_lang = subtitle[0].encode('utf_8').decode('unicode_escape')
                sub_name = file_name + '_' + subtitle_lang + '.srt'
            src_print(sub_name)
            CANDDY.download_bin(subtitle[1], WORK_DIR.file('Videos', sub_name))

    elif resource.type == 'Documents':
        if WORK_DIR.exist(file_name + '.pdf'): return
        pdf_url = re.search(r'textOrigUrl:"(.*?)"', res).group(1)
        src_print(file_name + '.pdf')
        CANDDY.download_bin(pdf_url, WORK_DIR.file(file_name + '.pdf'))

    elif resource.type == 'Rich texts':
        if WORK_DIR.exist(file_name + '.html'): return
        text = re.search(r'htmlContent:"(.*)",id', res.encode('utf_8').decode('unicode_escape'), re.S).group(1)
        src_print(file_name + '.html')
        with open(WORK_DIR.file(file_name + '.html'), 'w', encoding='utf_8') as file:
            file.write(text)


def start(url, path='', pdf=True, sub=True, files=True, text=True):
    """调用接口"""
    global CONFIG, WORK_DIR, RENAMER, VIDEOS

    course_info = get_summary(url)

    WORK_DIR = WorkingDir(path, course_info[1])
    WORK_DIR.change('Videos')
    RENAMER = Renamer(WORK_DIR.file('Rename.bat'))
    VIDEOS = ClassicFile(WORK_DIR.file('Videos.txt'))
    CONFIG = {'pdf': pdf, 'sub': sub, 'file': files, 'text': text}

    get_resource(course_info[0])


if __name__ == '__main__':
    # start('https://www.icourse163.org/course/NEU-1001956020', '', False)
    # start('https://www.icourse163.org/course/CSU-1002475002', '', pdf=False)
    start('https://www.icourse163.org/course/HIT-309001', r'F:\MOOCs')
    # start('https://www.icourse163.org/course/HIT-309001', r'')
    # start('https://www.icourse163.org/course/WHU-1002480002', '', True)
    pass
