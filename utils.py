import re
import os
import requests


class Resource(object):
    regex_sort = re.compile(r'^[第一二三四五六七八九十\d]+[\s\d\._\-章课节讲]*[\.\s、\-]\s*\d*')
    regex_file = re.compile(r'[\\/:\*\?"<>\|]')

    def __init__(self, id1, id2, id3, name, meta):
        self.name = Resource.regex_sort.sub('', name)
        self.id1 = id1
        self.id2 = id2
        self.id3 = id3
        self.meta = meta
        self.id = '%d.%d.%d' % (id1, id2, id3)

    @property
    def file_name(self):
        return self.id + ' ' + Resource.regex_file.sub('', self.name)

    def __str__(self):
        return self.name

    def operation(self, callback):
        callback(self)


class Video(Resource):
    def __init__(self, id1, id2, id3, name, meta, feature=None):
        super(Video, self).__init__(id1, id2, id3, name, meta)
        self.type = 'Video'
        self.feature = feature

    def operation(self, playlist, callback):
        playlist.write(self)
        callback(self)


class Document(Resource):
    def __init__(self, id1, id2, id3, name, meta, feature=None):
        super(Document, self).__init__(id1, id2, id3, name, meta)
        self.type = 'Documents'
        self.feature = feature


class RichText(Resource):
    def __init__(self, id1, id2, id3, name, meta, feature=None):
        super(RichText, self).__init__(id1, id2, id3, name, meta)
        self.type = 'Rich texts'
        self.feature = feature


class Attachment(Resource):
    def __init__(self, id1, id2, id3, name, meta, feature=None):
        super(Attachment, self).__init__(id1, id2, id3, name, meta)
        self.type = 'Attachment'
        self.feature = feature


class ClassicFile(object):
    def __init__(self, file):
        self._f = open(file, 'w', encoding='utf-8')
        self.file = file

    def write(self, string):
        self._f.write(string + '\n')

    def close(self):
        self._f.close()
        del self._f
        del self.file


def CourseDir(course_name, institution):
    return Resource.regex_file.sub('', '%s - %s' % (course_name, institution))


class Playlist(ClassicFile):
    def __init__(self):
        super(Playlist, self).__init__('Playlist.dpl')
        self._count = 0
        self._f.write('DAUMPLAYLIST\n\n')

    def write(self, video):
        self._count += 1
        self._f.write('%d*file*Videos\%s.mp4\n' % (self._count, video.file_name))
        self._f.write('%d*title*%s\n\n' % (self._count, '%d.%d %s' % (video.id1, video.id2, video.name)))


class Renamer(ClassicFile):
    def __init__(self, file):
        super(Renamer, self).__init__(file)
        self._f.write('CHCP 65001\n\n')

    def write(self, origin_name, file_name):
        self._f.write('REN "%s" "%s.mp4"\n' % (origin_name, file_name))


def parse_res_list(res_list, file=None, *operator):
    if file:
        with open(file, 'w', encoding='utf_8') as f:
            for res in res_list:
                f.write(str(res) + '\n')
        os.startfile(file)
        input('修改完文件名后按回车继续。')
        with open(file, encoding='utf_8') as f:
            for res in res_list:
                res.name = f.readline().rstrip('\n')
                res.operation(*operator)
    else:
        for res in res_list:
            res.operation(*operator)


class Crawler(requests.Session):
    header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36'}

    def __init__(self):
        super(Crawler, self).__init__()
        self.headers.update(Crawler.header)

    def set_cookies(self, cookies):
        requests.utils.add_dict_to_cookiejar(self.cookies, cookies)

    def download_bin(self, url, file_path, **kw):
        res = self.get(url, **kw).content
        with open(file_path, 'wb') as f:
            f.write(res)

    def download(self, url, file_path, **kw):
        res = self.get(url, **kw).text
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(res)


class Outline(ClassicFile):
    res_type = {'#': '【视频】', '!': '【附件】', '*': '【文档】', '+': '【富文本】', '': ''}

    def __init__(self):
        # 这里直接声明文件名是因为文件名基本不会改
        # 不管是什么时候，都是使用这个文件名
        # 要改的话就直接改这里就行了
        super(Outline, self).__init__('Outline.txt')

    def write(self, string, level=3, *number, sign=''):

        print('%s%s%s' % ('  ' * level, self.res_type[sign], string))
        name = '%s%s {%s}%s\n' % ('  ' * level, string, '.'.join(map(str, number)), sign)
        self._f.write(name)


class WorkingDir(object):
    def __init__(self, *base_dirs):
        # 从初始化的字符串中生成课程目录
        # 如果不存在课程目录的话就创建它
        # 并更改工作目录为这个目录
        base_dir = os.path.join(*base_dirs)
        if not os.path.isdir(base_dir):
            os.makedirs(base_dir)
        os.chdir(base_dir)
        self.base_dir = os.getcwd()
        self.path = ''

    def change(self, *relative):
        # 切换工作目录（假），可以接受多个目录名
        # 如果不存在该目录的话，就创建它
        self.path = os.path.join(self.base_dir, *relative)
        if not os.path.isdir(self.path):
            os.makedirs(self.path)

    def file(self, file_name):
        # 根据文件名返回一个完整的路径
        # 这个路径基于 chnage() 的目录
        return os.path.join(self.path, file_name)

    def exist(self, file_name):
        return os.path.exists(os.path.join(self.path, file_name))

    # def reset(self):
    # 将工作目录（假）切换回原来的目录
    # 这个函数其实是不必要的（因为只要不用这个类的对象就可以了）
    # self.path = self.base_dir


class Counter(object):
    """ 计数器 x.x.x """
    def reset():
        pass
    def __init__():
        self.a, self.b, self.c = 0
        


if __name__ == '__main__':
    pass
