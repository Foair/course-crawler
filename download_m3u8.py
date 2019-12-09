#!/usr/bin/env python3
import os
import sys
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download m3u8 to mp4')
    parser.add_argument('-l', default=r'', help='下载目录')
    parser.add_argument('-d', default=r'', help='下载目录')
    args = parser.parse_args()
    video_list = os.path.abspath(args.l)

    if args.d == '':
        video_dir = os.path.dirname(video_list)
    else:
        video_dir = os.path.abspath(args.d)

    with open(video_list) as f:
        lines = f.readlines()
        lines = [_.strip() for _ in lines if _ != '\n']
        for line in lines:
            name,url = line.split('\t')
            print(name,url)
            os.system('ffmpeg -i "{}" -c copy -bsf:a aac_adtstoasc "{}"'\
                      .format(url,os.path.join(video_dir,name)))