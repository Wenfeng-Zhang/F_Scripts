#-*- coding:utf8 -*-
#__author__ = 'wenfeng zhang'
#https://github.com/Wenfeng-Zhang

'''
import merge_short
toolbar = nuke.menu('Nodes')
m = toolbar.addMenu('F Script')
m.addCommand('Merge shot +', 'shuffle_Short.Shuffle_Short(1)', 'alt+up')
m.addCommand('Merge shot -', 'shuffle_Short.Shuffle_Short(-1)', 'alt+down')
'''

import nuke
def Shuffle_Short(shuffle_num=None):
    node = nuke.selectedNode()
    if not node or node.Class() != 'Shuffle':
        return False
    if node.Class() == "Shuffle":
        channel_list = [i for i in nuke.layers(node)]
        channel_name = node.knob('in').value()
        if channel_name in channel_list:
            num = (channel_list.index(channel_name)+shuffle_num) % len(channel_list)
            print(channel_list[num])
            node.knob('in').setValue(channel_list[num])
        else:
            node.knob('in').setValue('rgba')
            
            