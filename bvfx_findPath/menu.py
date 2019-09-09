#-*- coding:utf8 -*-
__author__ = 'wenfeng zhang'

from bvfx_findPath import *
toolbar = nuke.menu("Nodes")
m = toolbar.addMenu('F Script',)
m.addCommand('Locate files paths', 'bvfx_findPath(False)')