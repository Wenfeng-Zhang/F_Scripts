# -*- coding:utf8 -*-
#__author__ = Franklin Toussaint
import nuke, sys, subprocess

def versionSwith():
    flag = nuke.ask('Are you sure you want to switch the Nuke type?')
    if flag:
        nuke.scriptSave()
        nukeScript = nuke.scriptName()
        nukeExe = sys.executable
        if nuke.env['nukex'] == True:
            nukeProcess = subprocess.Popen([nukeExe, nukeScript])
        else:
            nukeProcess = subprocess.Popen([nukeExe, "--nukex", nukeScript])
        nuke.executeInMainThread(nuke.scriptExit)
if __name__ == "__main__":
    versionSwith()