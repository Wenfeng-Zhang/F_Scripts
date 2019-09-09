#-*- coding:utf8 -*-

import os,nuke
#你想要排除的文件夹,以字符串形式添加到列表里Exclude_Files
Exclude_Files = []
dirs = os.path.dirname(__file__)

dir_list = os.listdir(dirs)
for dir in dir_list:
    obj = os.path.join(dirs,dir)
    if os.path.isdir(obj) and dir not in Exclude_Files:
        nuke.pluginAddPath(obj)
