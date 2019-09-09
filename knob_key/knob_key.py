#-*- coding:utf8 -*-
#__author__ = 'wenfeng zhang'
#https://github.com/Wenfeng-Zhang

# import knob_key
# m = nuke.menu("Animation")
# m.addCommand("knob key", "knob_key.knob_key()",)


import nuke
def knob_key():
    f = nuke.frame()
    knob = nuke.thisKnob()
    value = knob.getValue()
    knob.setAnimated()
    if not isinstance(value,(list,tuple)):
        value = [value]
    for i in range(int(f-1),int(f+2)):
        for x in xrange(len(value)):
            knob.setValueAt(value[x],i,x)
        
if __name__ == "__main__":
    knob_key()