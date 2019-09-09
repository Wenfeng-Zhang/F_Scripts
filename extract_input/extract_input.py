#-*- coding:utf8 -*-
#__author__ = 'wenfeng zhang'
#https://github.com/Wenfeng-Zhang

#menu.py
#import extract_input


import nuke

def extract_input(num=None):
    #If num is None, all links are broken.
    if num == None:
        nodes = nuke.allNodes('Viewer')
        for node in nodes:
            for i in range(node.inputs()):
                node.setInput(i,None)
        return None
    #If the input is not a number, an error is returned.
    if not str(num).isdigit():
        raise Exception('Only integers can be entered.')
    #Disconnect the input connection channel, the default is the first channel.
    else:
        nodes = nuke.allNodes('Viewer')
        for node in nodes:
            node.setInput(int(num),None)
nuke.addOnScriptLoad(extract_input, args=0)