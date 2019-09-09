#-*- coding:utf8 -*-
#__author__ = 'wenfeng zhang'
#https://github.com/Wenfeng-Zhang

import node_disable

toolbar = nuke.menu("Nodes")
m = toolbar.addMenu('F Script/Node_Disable',)
m.addCommand('node_disable','node_disable.node_disable()','shift+k')
m.addCommand('clear_Constant_link','node_disable.clear_Constant_link()','ctrl+k')
m.addCommand('clear_the_linked_objects','node_disable.clear_the_linked_objects()')
m.addCommand('clear_the_outgoing_link','node_disable.clear_the_outgoing_link()')
m.addCommand('clear_all_link','node_disable.clear_all_link()')