cookie_str = 'UT=qRKARfIRiYYmExupfFD2pwhkIixANnCWaitf; BEC=f6c42c24d0c76e7acea242791ab87e34|1518172353|1518168348'

from utils import *
from bs4 import BeautifulSoup
import json
import re


def cookie_to_json(raw_cookies):
    cookies = {}

    for cookie in raw_cookies.split(';'):
        key, value = cookie.lstrip().split("=", 1)
        cookies[key] = value

    return cookies


cookies = cookie_to_json(cookie_str)

CANDY = Crawler()
CANDY.set_cookies(cookies)

counter = Counter()
outline = Outline()
video_list = []

# course_index = 'http://www.cnmooc.org/portal/course/11/8329.mooc'
# res = CANDY.get(course_index).text
# soup = BeautifulSoup(res, 'lxml')
# title = soup.find(class_='view-title substr').get_text(strip=True)
# university = soup.find(class_='person-attach substr').get_text(strip=True)
# print(CourseDir(title, university))

course_nav = 'http://www.cnmooc.org/portal/session/unitNavigation/8329.mooc'
res = CANDY.get(course_nav).text
soup = BeautifulSoup(res, 'lxml')
nav = soup.find(id='unitNavigation')
chapters = nav.find_all(class_='view-chapter')
for chapter in chapters:
    chapter_name = chapter.find(class_='chapter-text substr').get_text(strip=True)
    counter.add(0)
    outline.write(chapter_name, counter.one, 0)

    lectures = chapter.find_all(class_='view-lecture')
    for lecture in lectures:
        actions = lecture.find(class_='lecture-title')
        lecture_name = actions.get_text(strip=True)
        counter.add(1)
        outline.write(lecture_name, counter.two, 1)
        unitid = actions.a['unitid']
        # print(unitid)
        group = actions.div.find_all('a')
        # for action in group:
        #     print(action.i['class'])
        videos = list(filter(lambda action: 'icon-play' in action.i['class'][0], group))
        # videos = [action for action in group if lambda :'icon-play' in action.i['class'][0]]
        for video in videos:
            counter.add(2)
            outline.write(video['title'], str(counter), 2, sign='#')
            if len(videos) == 1:
                extra_num = ''
            else:
                extra_num = '-%s' % str(counter)[-1:]
            video_list.append(Video(str(counter), lecture_name + extra_num, video['itemid']))

for video in video_list:
    print(video.file_name)
#     res = CANDY.post('http://www.cnmooc.org/study/play.mooc', data={'itemId': video.meta, 'itemType': '10', 'testPaperId': ''}).text
#     soup = BeautifulSoup(res, 'lxml')
#     nodeId = soup.find(id='nodeId')['value']
#     print(nodeId)

#     res = CANDY.post('http://www.cnmooc.org/item/detail.mooc', data={'nodeId': nodeId, 'itemId': video.meta}).json()
#     print(res['node']['flvUrl'])
#     for ext in res['node']['nodeExts']:
#         print(ext['languageCode'])
#         print('http://static.cnmooc.org' + ext['node']['rsUrl'])

# res = CANDY.post('http://www.cnmooc.org/study/play.mooc', data={'itemId': '260176', 'itemType': '20', 'testPaperId': ''}).text
# pptx = re.search(r'isSlideShow\("(.+)?"\);', res).group(1)
# print('http://static.cnmooc.org' + pptx)
