#-*- coding:utf8 -*-
#__author__ = 'wenfeng zhang'
#https://github.com/Wenfeng-Zhang

#menu.py 
#import my_Localization

from nuke.localization import *
    
def my_Localization(num):
    if num == 0:
        resumeLocalization()
    elif num == 1:
        pauseLocalization()
my_Localization(1)

