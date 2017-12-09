---
layout: default
---

一个基于 Python 3 的 MOOC 课程爬虫，可以获取 [中国大学MOOC](http://www.icourse163.org/)、[学堂在线](http://www.xuetangx.com/)、[网易云课堂 MOOC](http://mooc.study.163.com/) 的免费课程，方便离线观看。目前可以获取到的资源有视频、富文本、附件和字幕。

虽然程序写的不怎么样，但是结构齐全、命名规范，可以方便定位和查找。

## 准备

目前只在 Windows 10 经过测试，而且不敢保证没有 bug。如果遇到有不能解析的课程，可以第一时间将课程的链接的链接发到我的邮箱 [master@foair.com](mailto:master@foair.com)，我会尽快修复。如果有任何好的建议也通过邮件和我联系。

请安装最新的 Python 3，并且使用 `pip` 安装两个库：`requests`，`BeautifulSoup`。

然后下载 zip 压缩文件（使用 Git 也是可以的），参照下面的各个文件的说明修改参数和保存路径。

`icourse.py`：中国大学MOOC

`study.py`：网易云课堂 MOOC

`xuetangx.py`：学堂在线

打开命令提示符输入命令就可以使用了。



## 中国大学MOOC



## 学堂在线



## 网易云课堂 MOOC

无法适用于网易云课堂的普通课程，只适用于 `mooc.study.163.com` 域下的课程。暂时没有写登录模块，现在只能使用 cookie 登录。不像中国大学MOOC那样，网易云课堂 MOOC 必须要登录才有权限查看和下载课程，所以登录的 cookies 务必设置。

找到如下行，

```python
COOKIES = {}
```

将 `{}` 之间替换为自己的 cookies，必须是字典格式。

如何获取字典格式的 cookies 呢？

用浏览器进入网易云课堂的首页，然后登录。打开一个 MOOC 课程的页面，比如 [程序设计入门—Java语言 - 网易云课堂](http://mooc.study.163.com/course/cloudclass-1000002014)。右键 ➔ 【审查元素】，然后切换到【Network】选项卡，然后点进入课程的学习按钮。回到【Network】那里，选择【Doc】，点第一个。然后往下滑，复制 `Cookie` 的内容。

