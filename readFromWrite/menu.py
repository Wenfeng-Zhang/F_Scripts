#-*- coding:utf-8 -*-
__author__ = 'wenfeng zhang'


import createRead
toolbar = nuke.menu("Nodes")
m = toolbar.addMenu('F Script',)
m.addCommand('Read from Write',
             'createRead.createRead()',
             'shift+r',
             icon="Read.png"
             )