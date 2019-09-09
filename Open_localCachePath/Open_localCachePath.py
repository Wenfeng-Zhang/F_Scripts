#-*- coding:utf8 -*-
#__author__ = 'wenfeng zhang'
#https://github.com/Wenfeng-Zhang
# data: 2019/7/17

'''
import Open_localCachePath
toolbar = nuke.menu("Nodes")
m = toolbar.addMenu("F Script")
m.addCommand("Open_localCachePath",  "Open_localCachePath.Open_localCachePath(nuke.selectedNode())",  "alt+z",  icon="Cached.png")
'''

import os,nuke
def Open_localCachePath(node):
    try:
        if node:
            localCachePath = nuke.toNode('preferences').knob('localCachePath').evaluate()

            filename = node.knob('file').evaluate()
            file_dirve = os.path.splitdrive(os.path.dirname(filename))[-1][1:]
            
            dirve = os.path.splitdrive(filename)[0][0]+'_'
            
            my_localCachePath = os.path.join(localCachePath, dirve, file_dirve)
            print my_localCachePath
            
            cmd = 'start "" "%s"' % my_localCachePath
            os.system(cmd)
        else:
            nuke.message('No nodes are selected.')
    except:
        pass
if __name__ == "__main__":
    Open_localCachePath(nuke.selectedNode())