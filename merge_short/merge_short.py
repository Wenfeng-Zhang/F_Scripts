#-*- coding:utf8 -*-
#__author__ = 'wenfeng zhang'
#https://github.com/Wenfeng-Zhang

'''
import merge_short
toolbar = nuke.menu('Nodes')
m = toolbar.addMenu('F Script')
m.addCommand('Merge shot', 'merge_short.Merge_Short()', 'alt+o')
'''

import nuke

def Merge_Short():
    operation_list = ['over', 'plus', 'screen']
    node = nuke.selectedNode()
    if node.Class() == "Merge2":
        operation_name = node.knob('operation').value()
        if operation_name in operation_list:
            num = (operation_list.index(operation_name)+1) % len(operation_list)
            print num
            node.knob('operation').setValue(operation_list[num])
        else:
            node.knob('operation').setValue('over')


            