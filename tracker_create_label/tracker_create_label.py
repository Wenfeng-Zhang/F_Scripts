#-*- coding:utf8 -*-
#__author__ = 'wenfeng zhang'
#https://github.com/Wenfeng-Zhang

#menu.py    
#import tracker_create_label

import nuke

def node_tracter():
    node = nuke.thisNode()
    knobNamelist = ['createPinUseCurrentFrame','createPinUseReferenceFrame','createPinUseCurrentFrameBaked','createPinUseReferenceFrameBaked','createTransformStabilize','createTransformMatchMove','createTransformStabilizeBaked','createTransformMatchMoveBaked']
    
    value1 = '''
  nodename = nuke.thisNode().name()
  frame = '%s%s.%s'%('[knob ', nodename,'reference_frame]')
  pin['label'].setValue('%s: %s'%("reference frame",frame))
'''

    value2='''
    frame = nuke.thisNode().knob('reference_frame').value()
    pin['label'].setValue('%s: %s'%("reference frame",str(int(frame)))
'''

    value3='''
nodename = nuke.thisNode().name()
frame = '%s%s.%s'%('[knob ', nodename,'reference_frame]')
transform['label'].setValue('%s: %s'%("reference frame",frame))
'''

    value4='''
frame = nuke.thisNode().knob('reference_frame').value()
transform['label'].setValue('%s: %s'%("reference frame",str(int(frame))))
'''


    for i in knobNamelist:
        text = node[i].value()
        
        if knobNamelist.index(i) in [0,1]:
            value = value1
         
        elif knobNamelist.index(i) in [2,3]:
            value = value2        
            
        elif knobNamelist.index(i) in [4,5]:
            value = value3
            
        elif knobNamelist.index(i) in [6,7]:
            value = value4
            
        value_text = '%s\n%s'%(text,value)
        node[i].setValue(value_text)
        
nuke.addOnCreate(node_tracter,nodeClass=('Tracker4'))
            