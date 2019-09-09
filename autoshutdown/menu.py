#-*- coding:utf8 -*-
#渲染完成后自动关机
from autoshutdown import addAsd,addAsdAR,asd,warn
nuke.addOnUserCreate(addAsd,nodeClass=('Write'))