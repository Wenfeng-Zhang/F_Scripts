#-*- coding:utf-8 -*-
__author__ = 'wenfeng zhang'


#��ݼ�����ʱ��ѭ��
from node_timer import *
toolbar = nuke.menu("Nodes")
m = toolbar.addMenu('F Script',)
m.addCommand('Node timer',
             'node_timer()',
             'shift+t')
