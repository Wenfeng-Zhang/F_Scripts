#-*- coding:utf8 -*-
#__author__ = 'wenfeng zhang'
#https://github.com/Wenfeng-Zhang

'''
import createRead
toolbar = nuke.menu("Nodes")
m = toolbar.addMenu('F Script',)
m.addCommand('Read from Write',
             'createRead.createRead()',
             'shift+r',
             icon="Read.png"
             )
'''

import os,re,nuke

def createRead():
    try:
        node = nuke.selectedNode()
        oldfile = node.knob('file').getValue()
        folder = os.path.dirname(oldfile)
        type_ = os.path.splitext(oldfile)[-1]
        name = os.path.basename(oldfile).split('.')[0]

        selectedNodeXpos = node.xpos()
        selectedNodeYpos = node.ypos()

        readNode = nuke.createNode('Read',inpanel=False)
        if re.search('(%\d*d)',oldfile):
            for seq in nuke.getFileNameList(folder):
                if re.search(name,seq) and re.search(type_, seq):
                    readNode.knob('file').fromUserText(os.path.join(folder,seq))
        else:
            readNode.knob('file').fromUserText(oldfile)

        readNode.setXpos(selectedNodeXpos)
        readNode.setYpos(selectedNodeYpos+60)
    except:
        pass