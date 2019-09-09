#-*- coding:utf-8 -*-
__author__ = 'wenfeng zhang'

if nuke.NUKE_VERSION_MAJOR >= 11:
    import timelineHotkeys
    toolbar = nuke.menu("Nodes")
    m = toolbar.addMenu('F Script')
    m.addCommand('Time Line Hotkeys', 'timelineHotkeys.main()')