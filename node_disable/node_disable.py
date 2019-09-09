#-*- coding:utf8 -*-
#__author__ = 'wenfeng zhang'
#https://github.com/Wenfeng-Zhang

'''
import node_disable

toolbar = nuke.menu("Nodes")
m = toolbar.addMenu('F Script/Node_Disable',)
m.addCommand('node_disable','node_disable.node_disable()','shift+k')
m.addCommand('clear_Constant_link','node_disable.clear_Constant_link()','ctrl+k')
m.addCommand('clear_the_linked_objects','node_disable.clear_the_linked_objects()')
m.addCommand('clear_the_outgoing_link','node_disable.clear_the_outgoing_link()')
m.addCommand('clear_all_link','node_disable.clear_all_link()')
'''

import nuke

# nodes = nuke.selectedNodes()

def node_disable():
    nodes = nuke.selectedNodes()
    x = []
    y = []
    
    for i in nodes:
        x.append(i.xpos())
        y.append(i.ypos())
        
    xpos = sum(x)/len(x)
    ypos = sum(y)/len(y)
    
    
    disabel_node = nuke.nodes.Constant(postage_stamp = 0, label = "<center><b>Disable")
    disabel_node.setXpos(xpos+200)
    disabel_node.setYpos(ypos)
    
    disabel_node_name = disabel_node['name'].value()
    
    for node in nodes:
        node['disable'].setExpression('%s%s%s'%('parent.',disabel_node_name,'.disable'))
        
########################################################################################
#删除与Constant节点相连节点的link
def clear_Constant_link():
    nodes = nuke.selectedNodes()
    for i in nodes:
        deps = nuke.dependencies(i, nuke.EXPRESSIONS)
        for knob_name in deps:
            if knob_name.Class() == "Constant":
                i.knob('disable').clearAnimated()
                
########################################################################################

#删除被link链接的节点的disable动画
def clear_the_linked_objects():
    nodes = nuke.selectedNodes()
    for i in nodes:
        deps = nuke.dependencies(i, nuke.EXPRESSIONS)
        if deps:
            i.knob('disable').clearAnimated()
            
########################################################################################
#删除从此处输入的link并删除节点
def clear_the_outgoing_link():
    nodes = nuke.selectedNodes()
    for i in nodes:
        ndeps = nuke.dependentNodes(nuke.EXPRESSIONS,i)
        for knob_name in ndeps:
            knob_name.knob('disable').clearAnimated()
        if i.Class() == "Constant":
            nuke.delete(i)
 
########################################################################################

def clear_all_link():
    [go for go in [clear_the_outgoing_link(),clear_the_linked_objects()]]
 
       
        