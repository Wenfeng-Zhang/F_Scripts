#-*- coding:utf8 -*-
__author__ = 'wenfeng zhang'

import FileCopy
toolbar = nuke.menu("Nodes")
m = toolbar.addMenu('F Script',)
m.addCommand("FileCopy" ,"FileCopy.main()","shift+C",icon="Write.png")