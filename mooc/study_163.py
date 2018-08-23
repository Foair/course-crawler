# -*- coding: utf-8 -*-
"""网易云课堂"""

import time
from .utils import *
from urllib import parse

CANDY = Crawler()
CONFIG = {}
FILES = {}

def get_summary(url):
    """从课程主页面获取信息"""

    res = requests.get(url).text

    course_id = re.search(r'courseId=(\d+)', url).group(1)
    name = re.search(r'<title>(.+) - 网易云课堂</title>', res).group(1)

    dir_name = course_dir(name, '网易云课堂')

    print(dir_name)

    CONFIG['course_id'] = course_id
    return course_id, dir_name

def parse_resource(resource):
    """解析资源地址和下载资源"""

    file_name = resource.file_name
    if resource.type == 'Video':
        post_data = {'callCount': '1', 'scriptSessionId':'${scriptSessionId}190',
                     'httpSessionId':'b1a6d411df364e51833ac11570fc3f07', 'c0-scriptName':'LessonLearnBean',
                     'c0-methodName':'getVideoLearnInfo', 'c0-id':'0', 'c0-param0':'string:' + resource.meta[1],
                     'c0-param1':'string:' + CONFIG['course_id'],
                     'batchId': str(int(time.time() * 1000))}
        res = CANDY.post('http://study.163.com/dwr/call/plaincall/LessonLearnBean.getVideoLearnInfo.dwr',
                         data=post_data).text.encode('utf_8').decode('unicode_escape')
        video_info = re.search(r'signature="(\w+)";.+videoId=(\d+);[\s\S]+name:"(.+?)",', res).group(1,2,3)
        data = CANDY.post('http://vod.study.163.com/eds/api/v1/vod/video', data={
            'videoId': video_info[1],
            'signature': video_info[0],
            'clientType': '1'
        }).text

        resolutions = ['shd', 'hd', 'sd']
        for sp in resolutions[CONFIG['resolution']:]:
            # TODO: 增加视频格式选择
            # video_info = re.search(r'%sUrl="(?P<url>.*?(?P<ext>\.((m3u8)|(mp4)|(flv))).*?)"' % sp, res)
            video_info = re.search(r'videoUrl":"(?P<url>http[^"]*?shd\.(?P<ext>.*?))"' % sp, res)
            if video_info:
                url, ext = video_info.group('url', 'ext')
                ext = '.' + ext
                break
        res_print(file_name + ext)
        FILES['renamer'].write(re.search(r'(\w+\.mp4)', mp4url).group(1), file_name, ext)
        FILES['video'].write_string(mp4url)

        if not CONFIG['sub']:
            return
        # 暂未发现字幕及其API

    else:
        if WORK_DIR.exist(file_name + resource.meta[2]):
            return
        res_print(file_name + resource.meta[2])
        CANDY.download_bin(resource.meta[3], WORK_DIR.file(file_name + resource.meta[2]))

def get_resource(course_id):
    """获取各种资源"""
    
    outline = Outline()
    playlist = Playlist()
    counter = Counter()

    video_list = []
    doc_list = []
    file_list = []

    post_data = {
                'callCount':1,
                'scriptSessionId':'${scriptSessionId}190',
                'httpSessionId':'89a04ce41c7d42759b0a62efe392e153',
                'c0-scriptName':'PlanNewBean',
                'c0-methodName':'getPlanCourseDetail',
                'c0-id': '0',
                'c0-param0':'string:' + course_id,
                'c0-param1':'number:0',
                'c0-param2':'null:null',
                'batchId':str(int(time.time() * 1000)),
                }
    res = CANDY.post('http://study.163.com/dwr/call/plaincall/PlanNewBean.getPlanCourseDetail.dwr',
                     data=post_data).text.encode('utf_8').decode('unicode_escape')
    print(res)
    chapters = re.findall(r'courseId=\d+;.+id=(\d+);.+name="(.+)";', res)
    for chapter in chapters:
        counter.add(0)
        outline.write(chapter[1], counter, 0)

        lessons = re.findall(r'chapterId='+ chapter[0] +';.+hasReferences=(\w+);.+id=(\d+);.+lessonName="(.+?)";', res)
        for lesson in lessons:
            counter.add(1)
            outline.write(lesson[2], counter, 1)

            # Video
            counter.add(2)
            outline.write(lesson[2], counter, 2, sign='#')
            video_list.append(Video(counter, lesson[2], lesson))
            counter.reset()

            # References
            docs = []
            files = []
            if eval(lesson[0][0].upper() + lesson[0][1:]):
                post_data = {'callCount': '1', 'scriptSessionId':'${scriptSessionId}190',
                             'httpSessionId':'b1a6d411df364e51833ac11570fc3f07', 'c0-scriptName':'LessonReferenceBean',
                             'c0-methodName':'getLessonReferenceVoByLessonId', 'c0-id':'0', 'c0-param0':'number:' + lesson[1],
                             'batchId': str(int(time.time() * 1000))}
                ref_info = CANDY.post('http://study.163.com/dwr/call/plaincall/LessonReferenceBean.getLessonReferenceVoByLessonId.dwr',
                                 data=post_data).text.encode('utf_8').decode('unicode_escape')
                refs = re.findall(r'id=(\d+);.+name="(.+)";.+suffix="(\.\w+)";.+url="(.+?)";', ref_info)

                for ref in refs:
                    ref = (ref[0], parse.unquote(ref[1]), ref[2], ref[3])
                    if ref[2] in ['.ppt', '.doc', '.pdf', '.docx']:
                        docs.append(ref)
                    else:
                        files.append(ref)
            ## Doc
            for doc in docs:
                counter.add(2)
                outline.write(doc[1], counter, 2, sign='*')
                if CONFIG['doc']:
                    doc_list.append(Document(counter, doc[1], doc))
            counter.reset()

            ## File
            for file in files:
                counter.add(2)
                outline.write(file[1], counter, 2, sign='!')
                if CONFIG['file']:
                    file_list.append(Resource(counter, file[1], file))
            counter.reset()

    if video_list:
        rename = WORK_DIR.file('Names.txt') if CONFIG['rename'] else False
        WORK_DIR.change('Videos')
        if CONFIG['dpl']:
            parse_res_list(video_list, rename, playlist.write, parse_resource)
        else:
            parse_res_list(video_list, rename, parse_resource)
    if doc_list:
        WORK_DIR.change('DOCs')
        parse_res_list(doc_list, None, parse_resource)
    if file_list:
        WORK_DIR.change('Files')
        parse_res_list(file_list, None, parse_resource)

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

    WORK_DIR.change('Videos')
    FILES['renamer'] = Renamer(WORK_DIR.file('Rename.bat'))
    FILES['video'] = ClassicFile(WORK_DIR.file('Videos.txt'))

    # 获得资源
    get_resource(course_info[0])
