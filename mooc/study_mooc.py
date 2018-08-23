# -*- coding: utf-8 -*-
"""网易云课堂 MOOC"""

import time
from .utils import *

CANDY = Crawler()
CONFIG = {}
FILES = {}


def get_summary(url):
    """从课程主页面获取信息"""

    res = CANDY.get(url).text

    term_id = re.search(r'termId : "(\d+)"', res).group(1)
    names = re.findall(r'name:"(.+)"', res)

    dir_name = course_dir(names[0], names[1])

    print(dir_name)

    CONFIG['term_id'] = term_id
    return term_id, dir_name


def get_announce(term_id):
    """ 获取课程的公告 """

    post_data = {'callCount': '1', 'scriptSessionId': '${scriptSessionId}190',
                 'httpSessionId': 'dba4977be78d42a78a6e2c2dd2b9bb42', 'c0-scriptName': 'CourseBean',
                 'c0-methodName': 'getAllAnnouncementByTerm', 'c0-id': '0', 'c0-param0': 'number:' + term_id,
                 'c0-param1': 'number:1', 'batchId': str(int(time.time() * 1000))}
    res = CANDY.post('http://mooc.study.163.com/dwr/call/plaincall/CourseBean.getAllAnnouncementByTerm.dwr',
                     data=post_data).text
    announcements = re.findall(r'content="(.*?[^\\])".*title="(.*?[^\\])"', res)

    with open('Announcements.html', 'w', encoding='utf-8') as announce_file:
        for announcement in announcements:
            # 公告内容
            announce_content = announcement[0].encode('utf-8').decode('unicode_escape')

            # 公告标题
            announce_title = announcement[1].encode('utf-8').decode('unicode_escape')
            announce_file.write('<h1>' + announce_title + '</h1>\n' + announce_content + '\n')


def parse_resource(resource):
    """解析资源地址和下载资源"""

    post_data = {'callCount': '1', 'scriptSessionId': '${scriptSessionId}190',
                 'httpSessionId': 'b8efd4c73fd1434896507b83de631f0f', 'c0-scriptName': 'CourseBean',
                 'c0-methodName': 'getLessonUnitLearnVo', 'c0-id': '0', 'c0-param0': 'number:' + CONFIG['term_id'],
                 'c0-param1': 'number:' + resource.meta[0], 'c0-param2': 'number:' + resource.meta[1],
                 'c0-param3': 'number:0', 'c0-param4': 'number:' + resource.meta[2],
                 'batchId': str(int(time.time() * 1000))}
    res = CANDY.post('http://mooc.study.163.com/dwr/call/plaincall/CourseBean.getLessonUnitLearnVo.dwr',
                     data=post_data).text

    file_name = resource.file_name
    if resource.type == 'Video':
        signature = re.search(r'signature="(.+?)"', res).group(1)
        data = CANDY.post('https://vod.study.163.com/eds/api/v1/vod/video', data={
            'videoId': resource.meta[0],
            'signature': signature,
            'clientType': '1'
        }).text
        mp4url = (re.search(r'videoUrl":"(http[^"]*?shd\.mp4.*?)"', data) or
                  re.search(r'videoUrl":"(http[^"]*?hd\.mp4.*?)"', data) or
                  re.search(r'videoUrl":"(http[^"]*?sd\.mp4.*?)"', data)).group(1)
        res_print(file_name + '.mp4')
        FILES['renamer'].write(re.search(r'(\w+\.mp4)', mp4url).group(1), file_name)
        FILES['video'].write_string(mp4url)

        if not CONFIG['sub']:
            return
        subtitles = re.findall(r'name="(.+)";.*url="(.*?)"', res)
        WORK_DIR.change('Videos')
        for subtitle in subtitles:
            if len(subtitles) == 1:
                sub_name = file_name + '.srt'
            else:
                subtitle_lang = subtitle[0].encode('utf_8').decode('unicode_escape')
                sub_name = file_name + '_' + subtitle_lang + '.srt'
            res_print(sub_name)
            CANDY.download_bin(subtitle[1], WORK_DIR.file(sub_name))

    elif resource.type == 'Document':
        if WORK_DIR.exist(file_name + '.pdf'):
            return
        pdf_url = re.search(r'textOrigUrl:"(.*?)"', res).group(1)
        res_print(file_name + '.pdf')
        CANDY.download_bin(pdf_url, WORK_DIR.file(file_name + '.pdf'))

    elif resource.type == 'Rich':
        if WORK_DIR.exist(file_name + '.html'):
            return
        text = re.search(r'htmlContent:"(.*)",id', res.encode('utf_8').decode('unicode_escape'), re.S).group(1)
        res_print(file_name + '.html')
        with open(WORK_DIR.file(file_name + '.html'), 'w', encoding='utf_8') as file:
            file.write(text)


def get_resource(term_id):
    """获取各种资源"""

    outline = Outline()
    playlist = Playlist()
    counter = Counter()

    video_list = []
    pdf_list = []
    rich_text_list = []

    post_data = {'callCount': '1', 'scriptSessionId': '${scriptSessionId}190',
                 'httpSessionId': 'b8efd4c73fd1434896507b83de631f0f', 'c0-scriptName': 'CourseBean',
                 'c0-methodName': 'getLastLearnedMocTermDto', 'c0-id': '0', 'c0-param0': 'number:' + term_id,
                 'batchId': str(int(time.time() * 1000))}
    res = CANDY.post('http://mooc.study.163.com/dwr/call/plaincall/CourseBean.getLastLearnedMocTermDto.dwr',
                     data=post_data).text.encode('utf_8').decode('unicode_escape')

    chapters = re.findall(r'homeworks=\w+;.+id=(\d+).+name="(.+)";', res)
    for chapter in chapters:
        counter.add(0)
        outline.write(chapter[1], counter, 0)

        lessons = re.findall(r'chapterId=' + chapter[0] + r'.+contentType=1.+id=(\d+).+name="(.+)".+test', res)
        for lesson in lessons:
            counter.add(1)
            outline.write(lesson[1], counter, 1)

            videos = re.findall(r'contentId=(\d+).+contentType=(1).+id=(\d+).+lessonId=' +
                                lesson[0] + r'.+name="(.+)"', res)
            for video in videos:
                counter.add(2)
                outline.write(video[3], counter, 2, sign='#')
                video_list.append(Video(counter, video[3], video))
            counter.reset()

            pdfs = re.findall(r'contentId=(\d+).+contentType=(3).+id=(\d+).+lessonId=' +
                              lesson[0] + r'.+name="(.+)"', res)
            for pdf in pdfs:
                counter.add(2)
                outline.write(pdf[3], counter, 2, sign='*')
                if CONFIG['doc']:
                    pdf_list.append(Document(counter, pdf[3], pdf))
            counter.reset()

            rich_text = re.findall(r'contentId=(\d+).+contentType=(4).+id=(\d+).+jsonContent=(.+);.+lessonId=' +
                                   lesson[0] + r'.+name="(.+)"', res)
            for text in rich_text:
                counter.add(2)
                outline.write(text[4], counter, 2, sign='+')
                if CONFIG['text']:
                    rich_text_list.append(RichText(counter, text[4], text))
                if CONFIG['file']:
                    if text[3] != 'null' and text[3] != '""':
                        params = {'nosKey': re.search('nosKey":"(.+?)"', text[3]).group(1),
                                  'fileName': re.search('"fileName":"(.+?)"', text[3]).group(1)}
                        file_name = Resource.file_to_save(params['fileName'])
                        outline.write(file_name, counter, 2, sign='!')

                        WORK_DIR.change('Files')
                        res_print(params['fileName'])
                        file_name = '%s %s' % (counter, file_name)
                        CANDY.download_bin('https://www.icourse163.org/course/attachment.htm',
                                           WORK_DIR.file(file_name), params=params)
            counter.reset()

    if video_list:
        rename = WORK_DIR.file('Names.txt') if CONFIG['rename'] else False
        WORK_DIR.change('Videos')
        if CONFIG['dpl']:
            parse_res_list(video_list, rename, playlist.write, parse_resource)
        else:
            parse_res_list(video_list, rename, parse_resource)
    if pdf_list:
        WORK_DIR.change('PDFs')
        parse_res_list(pdf_list, None, parse_resource)
    if rich_text_list:
        WORK_DIR.change('Texts')
        parse_res_list(rich_text_list, None, parse_resource)


def start(url, config, cookies=None):
    """调用接口函数"""

    # 初始化设置
    global WORK_DIR
    CANDY.set_cookies(cookies)
    CONFIG.update(config)

    # 课程信息
    course_info = get_summary(url)

    # 创建课程目录
    WORK_DIR = WorkingDir(CONFIG['dir'], course_info[1])

    # 课程公告
    get_announce(course_info[0])

    WORK_DIR.change('Videos')
    FILES['renamer'] = Renamer(WORK_DIR.file('Rename.bat'))
    FILES['video'] = ClassicFile(WORK_DIR.file('Videos.txt'))

    # 获得资源
    get_resource(course_info[0])
