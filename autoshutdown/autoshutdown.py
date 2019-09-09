###############
###############

#AUTOSHUTDOWN___BY MOHANPUGAZ
#created on 06-06-2015 2:40 am
#mail me mohanpugaz@gmail.com""" 

##############

# This Script Shutdowns the computer after render completed
# Check the write node tabs after instalation 
# Mark the autoshutdown checkbox to make shutdown after render completed

##############
#for menu.py (without #)
#
#
#from autoshutdown import addAsd,addAsdAR,asd,warn
#nuke.addOnUserCreate(addAsd,nodeClass=('Write'))
#
##############
##############



import nuke
import subprocess as sp

def asd():
    nuke.scriptSave()
    sp.call(["shutdown","-f","-s","-t","30","-c","\"This is Autoshutdown for Nuke by Mohan pugaz\""])
    return

def addAsd():
    
    newTab=nuke.Tab_Knob('M_tab')    
    newKnob=nuke.Boolean_Knob("Auto_Shutdown")
    
    node=nuke.thisNode()
    node.addKnob(newTab)
    node.addKnob(newKnob)
    node['beforeRender'].setValue(r'addAsdAR(),warn()')




def addAsdAR():

    node=nuke.selectedNode()
    val=node['Auto_Shutdown'].getValue()
    print val
   
    if val==1:
        node['afterRender'].setValue(r'asd()')
       
    else:
        node['afterRender'].setValue('')
    
    return 

def warn():
    node=nuke.selectedNode()
    val=node['Auto_Shutdown'].getValue()
    if val==1 :
        ask=nuke.ask('Autoshutdown is turned on are you sure want to shutdown?')
        if ask==True:
            node['afterRender'].setValue(r'asd()')
        elif ask==False:
            node['afterRender'].setValue('')
    else :
        pass
    return node


