#-*- coding:utf8 -*-
#__author__ = 'wenfeng zhang'
#https://github.com/Wenfeng-Zhang

#menu.py
#from new_save_class import *

import nuke
import nukescripts
import os

def script_name(name=''):
    if name:
        name = os.path.basename(name.split('.')[0])
#        print name
        return name
    return None

#script_name(nuke.filename(nuke.selectedNode()))

def customSave(mode = 'save'):
    if mode == 'save':
        nuke.scriptSave("")

    elif mode ==  'saveAs':
        nuke.scriptSaveAs("")
        
    elif mode == "saveNewVersion":
        write_list = [write for write in nuke.allNodes('Write') if script_name(nuke.filename(write))==script_name(nuke.scriptName())]
        nukescripts.script_and_write_nodes_version_up()
        if write_list:
            selectedNodes = nuke.selectedNodes()[:]
            nukescripts.clear_selection_recursive()
            for write in write_list:
                write.setSelected(True)
                nukescripts.version_up()
                write.setSelected(False)
            for node in selectedNodes:
                node.setSelected(True)
            nuke.scriptSave("")
                
                
                
#replace menu items (if you're using nuke 8 or older you have to change the names of menus)
# nuke.menu('Nuke').findItem('File/Save Comp').setScript('customSave()')
# nuke.menu('Nuke').findItem('File/Save Comp As...').setScript('customSave("saveAs")')
nuke.menu('Nuke').findItem('File/Save New Comp Version').setScript('customSave("saveNewVersion")')