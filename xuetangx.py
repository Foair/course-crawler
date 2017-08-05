# Foair
# 2017年5月15日

import re
import os
import sys
import json
import getpass
import requests
from bs4 import BeautifulSoup

# 用户名或邮箱
ACCOUNT = '873669965@qq.com'
# 可以设置密码，没有密码在登录时需要输入密码
PASSWORD = None

BASEURL = 'http://www.xuetangx.com'
CONNECT = requests.Session()
CONNECT.headers.update({'User-Agent': 'Mozilla/5.0'})
# 匹配课程编号的正则表达式
NAME = re.compile(r'^[第一二三四五六七八九十\d]+[\s\d\._章课节讲]*[\.\s、]\s*\d*')
# 连续两个以上的空白字符正则表达式
RMSPACE = re.compile(r'\s+')
# Windows 文件名非法字符的正则表达式
FILENAME = re.compile(r'[\\/:\*\?"<>\|]')


def login(account, pwd):
    '进行用户认证'
    if not pwd:
        pwd = getpass.getpass('输入密码：')
    loginaddr = 'http://www.xuetangx.com/v2/login_ajax'
    data = {'username': account, 'password': pwd, 'remember': 'true'}
    back = CONNECT.post(loginaddr, data=data)
    if back.json()['success']:
        print('验证成功！')
    else:
        print('登录信息不正确！')
        sys.exit(1)
    with open('cookies.json', 'w') as cookiefile:
        json.dump(CONNECT.cookies.get_dict(), cookiefile)


def main():
    '准备工作开始'
    if os.path.exists('cookies.json'):
        print('本地存在 cookies 文件……')
        with open('cookies.json') as cookiefile:
            cookies = json.load(cookiefile)
        requests.utils.add_dict_to_cookiejar(CONNECT.cookies, cookies)
        status = CONNECT.get('http://www.xuetangx.com/header_ajax')
        if status.json()['login']:
            print('验证成功！')
        else:
            print('本地 cookies 文件失效，获取新的 cookies……')
            login(ACCOUNT, PASSWORD)
    else:
        login(ACCOUNT, PASSWORD)
    addr = input('输入课程的地址：')
    # 获取课程的标题
    about_page = CONNECT.get(addr).text
    title = BeautifulSoup(about_page, 'lxml').find(id='title1').string
    print(title)
    title = FILENAME.sub('', title)
    # 创建文件夹
    try:
        os.mkdir(title)
    except FileExistsError:
        print('课程已经存在，采用分析模式……')
    # 进入课件页面
    addr = addr.rstrip('about') + 'courseware'
    return addr


def download(link, name):
    '根据文档相对地址来下载文件，并命名'
    res = CONNECT.get(BASEURL + link)
    with open(name, 'wb') as resfile:
        resfile.write(res.content)


def getcontent(url):
    flag1 = 0
    flag2 = 0
    flag3 = 0
    courseware = CONNECT.get(url).text
    soup = BeautifulSoup(courseware, 'lxml')
    chapters = soup.find(id='accordion').find_all(class_='chapter')
    cnt1 = 1
    for chapcnt, chapter in enumerate(chapters, 1):
        chapname = chapter.h3.a.get_text(strip=True)
        secs = chapter.select('ul a')
        print('%s' % chapname)
        cnt2 = 1
        for seccnt, sec in enumerate(secs, 1):
            sec_url = BASEURL + sec['href']
            sec_title = sec.p.string.strip()
            print('  %s' % sec_title)
            # 每个具体的页面
            detail = CONNECT.get(sec_url).text
            soup = BeautifulSoup(detail, 'lxml')
            reses = soup.find(id='sequence-list').find_all('li')
            COURSE_REGX = re.compile('data-ccsource=.(\w+).')
            tabcnt = 0
            cnt3 = 0
            for res in reses:
                # print(res.a.get('data-page-title'))
                # if i == 0: # 每一个标签页
                seq = res.a.get('aria-controls')
                contents = soup.find(id=seq)
                tab = BeautifulSoup(contents.string, 'lxml').div.div
                # with open('tab.html', 'w', encoding='utf-8') as f:
                #     f.write(tab.prettify())
                for tab in tab.find_all('div', class_='xblock'):
                    video_per_tab = 0
                    # 标签页的每一个区块
                    types = tab['data-type']
                    if types == 'Problem' or types == 'InlineDiscussion' or types == 'HTMLModule':
                        continue
                    # print(tab)
                    name = tab.h2.string.strip()
                    if name == 'Video':
                        tabcnt += 1
                        if tabcnt == 1:
                            name = NAME.sub('', sec_title)
                        else:
                            name = '%s（%d）' % (NAME.sub('', sec_title), tabcnt)
                    if types == 'Video':
                        cnt3 += 1
                        flag2 = 1
                        flag3 = 1
                        video_per_tab += 1
                        if video_per_tab != 1:
                            name = '%s-%d' % (name, video_per_tab)
                        video_id = tab.div['data-ccsource']
                        print('------->', name)
                        getvideo(video_id, '%d.%d.%d %s' % (cnt1, cnt2, cnt3,
                                                            name))

            if flag2 == 1:
                cnt2 += 1
                flag2 = 0

        if flag3 == 1:
            cnt1 += 1
            flag3 = 0


def getvideo(video_id, name):
    name = FILENAME.sub('', name)
    name = RMSPACE.sub(' ', name)
    res = CONNECT.get('https://xuetangx.com/videoid2source/' + video_id).text
    video_url = json.loads(res)['sources']['quality20'][0]
    Links.write(re.search(r'(.+-20.mp4)', video_url).group(1) + '\n')
    Renamer.write('rename "' + re.search(r'(\w+-20.mp4)', video_url).group(1) +
                  '" "%s.mp4"\n' % name)


if __name__ == '__main__':
    Links = open('Links.txt', 'w', encoding='utf-8')
    Renamer = open('Rename.bat', 'w', encoding='utf-8')
    Renamer.write('chcp 65001\n')
    Toc = open('ToC.txt', 'w', encoding='utf-8')
    getcontent(main())
    Links.close()
    Renamer.close()
    Toc.close()
