#-*- coding:utf-8 -*-
__author__ = 'wenfeng zhang'


#快捷键创建时间循环
from node_timer import *
toolbar = nuke.menu("Nodes")
m = toolbar.addMenu('F Script',)
m.addCommand('Node timer',
             'node_timer()',
             'shift+t')
