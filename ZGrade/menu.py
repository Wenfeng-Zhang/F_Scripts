#-*- coding:utf8 -*-
__author__ = 'wenfeng zhang'

import ZGrade
toolbar = nuke.menu("Nodes")
m = toolbar.addMenu('F Script',)
m.addCommand('ZGrade','ZGrade.main()',icon="Clamp.png")