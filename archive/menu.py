#-*- coding:utf8 -*-
__author__ = 'wenfeng zhang'

import nuke
import archive
toolbar = nuke.menu("Nodes")
m = toolbar.addMenu('F Script',)
m.addCommand("archive","archive._archiveThisComp()")