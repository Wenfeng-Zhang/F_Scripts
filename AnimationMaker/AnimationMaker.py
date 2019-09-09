#-*- coding:utf-8 -*-
#694-->"updateUI",2214 --> node['updateUI'].setValue(None)

##################################################################################
#                                                                                #
#                             ANIMATION MAKER 1.3                                #
#                               David Emeny 2017                                 #
#                                                                                #
# This is a python/pyside extension to Nuke giving you prebuilt ease and wave    #
# expressions on any animatable knob. Just right click the knob and choose       #
# 'Animation maker...' from the pop up menu to display the interactive dialog.   #
# When you've tailored your animation, click CREATE and the expression required  #
# to produce that animation curve will be set on the knob in question.           #
# A custom tab will appear on the node too, so you can tweak your animation with #
# sliders. Click the EDIT button if you want to choose a different animation     #
# type. You can set Animation on any number of knobs within the same node.       #
# Clicking the REMOVE button removes a tab, but leaves the expression intact,    #
# using the last values you chose. The RESTORE button removes the tab and sets   #
# it back to the original value/curve. User presets are stored in an xml file    #
# alongside this script.                                                         #
#                                                                                #
# Now works in Nuke 11, and is backwards compatible with Nuke 10 and below.      #
##################################################################################


################# INSTALL INSTRUCTIONS ###################
# Copy this file to your .nuke folder or plugins folder  #
# Add this line to your menu.py:                         #
# import AnimationMaker                                  #
##########################################################


import nuke

try:
    # < Nuke 11
    import PySide.QtCore as QtCore
    import PySide.QtGui as QtGui
    import PySide.QtGui as QtGuiWidgets
except:
    # >= Nuke 11
    import PySide2.QtCore as QtCore
    import PySide2.QtGui as QtGui
    import PySide2.QtWidgets as QtGuiWidgets

import random
import time
import math
import thread
import os
import xml.etree.ElementTree as xml
from xml.dom import minidom
import ast #for handling lists in presets

#on importing this module, add an item in the Animation menu
nuke.menu('Animation').addCommand( 'Animation Maker...', 'AnimationMaker.showWindow()','',icon='ParticleBounce.png')


def showWindow(knobName = None, knobIndex = None):
    
    #if no knobname is sent, this is called from the right click menu not a button
    if knobName == None:
        k = nuke.thisKnob()
    else:
        k = nuke.thisNode()[knobName]
    
    
    #see if there's more than one value (eg: x,y)
    if knobIndex == -1 or knobIndex == None:
        try:
            knobNames = []
            for i in range(0,len(k.value())):
                knobNames.append(k.name() + '.' + k.names(i))

            #ask user to choose one
            p = nuke.Panel("Which value?")
            p.addEnumerationPulldown("Knob value:", ' '.join(knobNames))
            
            p.addButton("Cancel")
            p.addButton("OK")
            pResult = p.show()
            
            if pResult == 1:
                #if OK was pressed, do stuff
                knobIndex = knobNames.index(p.value("Knob value:"))
                animationWindow(k.name(),knobIndex)

        except:
            #no sub knobs found, so open as normal
            animationWindow(k.name())
    else:
            animationWindow(k.name(),knobIndex)

    

class animationWindow(QtGuiWidgets.QWidget):
    
    def __init__(self, knobName, knobIndex = -1, parent=None):
        
        super(animationWindow, self).__init__()
        self.setWindowFlags(QtCore.Qt.Window)
        #make sure the widget is deleted when closed, so nuke doesn't crash on exit
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        
        self.theNode = nuke.thisNode()
        self.theKnob = self.theNode[knobName]
        self.origKnobName = knobName
        self.theKnobName = knobName

        #see if it's a multiple value knob
        try:
            self.knobAmount = len(self.theKnob.value())
        except:
            self.knobAmount = 1
            
        self.updateCreateButtonPressed = False
        
        #save the original value/keyframes/expression on that knob
        #so we can put it back again if they cancel
        self.originalValue = self.theKnob.toScript()
        
        self.knobIndex = knobIndex
        if self.knobIndex > -1:
            #there is more than one knob
            self.theKnobName += '.' + self.theKnob.names(self.knobIndex)
            self.originalValues = toScriptMultiple(self.originalValue)
        else:
            self.originalValues = None
        
        
        #check if called from a knob that already has an associated tab
        theKnobs = self.theNode.knobs()
        if ("anim_tab_" + self.theKnobName) in theKnobs:
            self.editMode = True
        else:
            self.editMode = False
    
        if self.editMode:
            #check which kind of animation it is
            try:
                self.animType = self.theNode['a_animType_' + self.theKnobName].value()
            except:
                self.animType = "ease"
        else:
            self.animType = "ease"

        #set up colour scheme
        self.main_colour = (48,138,165)
        self.alt_colour = (255,100,100)
        self.main_colour_style = '1f5884'
        self.bg_colour_style = '354450'

        #set up window
        self.width = 600
        self.height = 700
        self.setGeometry(800, 200, self.width, self.height)
        self.setWindowTitle('Animation Maker - %s.%s' %(self.theNode.name(),self.theKnobName))
        self.setStyleSheet('QWidget { background-color: #%s }' % self.bg_colour_style)
        
        #make close button
        if self.editMode:
            self.closeButton = QtGuiWidgets.QPushButton('UPDATE', self)
        else:
            self.closeButton = QtGuiWidgets.QPushButton('CREATE', self)
    
        self.closeButton.setGeometry(self.width-120, self.height-440, 100, 50)
        self.closeButton.setStyleSheet('QWidget { background-color: #%s }' % self.main_colour_style)
        self.closeButton.clicked.connect(self.closeButtonPressed)

        #make choice buttons
        buttonFont = QtGui.QFont("Verdana", 15, QtGui.QFont.Bold)
 
        self.waveButton = QtGuiWidgets.QPushButton('Wave', self)
        self.waveButton.setGeometry(0, 0, self.width/2, 50)
        self.waveButton.setFont(buttonFont)
        self.waveButton.clicked.connect(self.waveButtonPressed) 
        
        self.easeButton = QtGuiWidgets.QPushButton('Ease', self)
        self.easeButton.setGeometry(self.width/2, 0, self.width/2, 50)
        self.easeButton.setFont(buttonFont)
        self.easeButton.clicked.connect(self.easeButtonPressed)

        #highlight relevant button
        if self.animType == "ease":
            self.easeButton.setStyleSheet('QWidget { background-color: #%s }' % self.main_colour_style)
        elif self.animType == "wave" or self.animType == "waveEase":
            self.waveButton.setStyleSheet('QWidget { background-color: #%s }' % self.main_colour_style)

        #make copyright text
        self.copyrightLabel = QtGuiWidgets.QLabel(self)
        self.copyrightLabel.setText('<p style="font-family:arial;color:gray;font-size:10px;">AnimationMaker 1.3 - David Emeny 2017</p>')
        self.copyrightLabel.move(6, self.height-388)
    
        self.easeBoxes = []
        self.waveBoxes = []

        self.setUpEaseBoxes()
    
        #set up different boxes if editing from wave or waveEase
        if self.editMode:
            if self.animType == "wave" or self.animType == "waveEase":

                if len(self.waveBoxes) > 0:
                    self.showWaveBoxes()
                else:
                    self.setUpWaveBoxes()
                    self.showWaveBoxes()
                
                self.hideEaseBoxes()
                

        #PRESET PULLDOWN
        #get list of presets
        preset_list = read_preset_list()
        if preset_list:
            preset_list.insert(0,"--- new ---")
        else:
            preset_list = ["--- new ---"]
            
        self.presetLabel = QtGuiWidgets.QLabel(self)
        self.presetLabel.setText('Preset')
        self.presetLabel.move(self.width/2+2, 60)
        self.presetBox = MyComboBox(self) 
        self.presetBox.addItems(preset_list)
        self.presetBox.setGeometry(self.width/2, self.presetLabel.y()+15,278,20)
        
        if self.editMode:
            try:
                theIndex = self.presetBox.findText(self.theNode['a_preset_'+self.theKnobName].value(),QtCore.Qt.MatchExactly)
                self.presetBox.setCurrentIndex(theIndex)
            except:
                pass
                    
        self.presetBox.currentIndexChanged.connect(self.presetChanged)
        self.presetBox.highlighted.connect(self.presetChanged)
        self.presetBox.activated.connect(self.presetChanged)
        self.presetBoxOld = self.presetBox.currentText()

        #PRESET BUTTONS
        self.presetReloadButton = QtGuiWidgets.QPushButton('reload preset', self)
        self.presetReloadButton.setGeometry(self.width/2, self.presetBox.y()+25, 89, 20)
        self.presetReloadButton.clicked.connect(self.reloadPreset)

        self.presetUpdateButton = QtGuiWidgets.QPushButton('save preset', self)
        self.presetUpdateButton.setGeometry(self.width/2+97, self.presetBox.y()+25, 85, 20)
        self.presetUpdateButton.clicked.connect(self.save_preset_to_file)

        self.presetDeleteButton = QtGuiWidgets.QPushButton('delete preset', self)
        self.presetDeleteButton.setGeometry(self.width/2+190, self.presetBox.y()+25, 88, 20)
        self.presetDeleteButton.clicked.connect(self.delete_preset_from_file)

    
        #make view
        self.view = QtGuiWidgets.QGraphicsView(self)
        self.view.setRenderHint(QtGui.QPainter.Antialiasing)
        self.view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        #make view fit the widget size
        self.viewYoffset = 325 #225
        self.view.setGeometry(0, self.viewYoffset, self.width, self.height - self.viewYoffset)

        #make scene 
        self.scene = QtGuiWidgets.QGraphicsScene(self)
        #make scene fit the view size
        self.scene.setSceneRect(QtCore.QRect(0, 0, self.view.width(), self.view.height()))
        #set scene background colour
        self.scene.setBackgroundBrush(QtGui.QColor(0,0,0))
        #add scene to the view
        self.view.setScene(self.scene)
    
        #add lines
        self.viewTop = 0 #115
        self.boxheight = self.view.height() / 2
        self.boxwidth = self.width / 3
        self.line1 = lineGraphic(self, 0.0,self.boxheight,self.width,self.boxheight, QtGui.QColor(100,100,100))
        self.scene.addItem(self.line1)
        self.line2 = lineGraphic(self, self.boxwidth,self.viewTop,self.boxwidth,self.boxheight, QtGui.QColor(100,100,100))
        self.scene.addItem(self.line2)
        self.line3 = lineGraphic(self, self.boxwidth*2,self.viewTop,self.boxwidth*2,self.boxheight, QtGui.QColor(100,100,100))
        self.scene.addItem(self.line3)
        
        self.plot_yMax = self.boxheight+30.0
        self.plot_yMin = self.view.height()-33.0 #450.0
        self.plot_xMin = 30
        self.plot_xMax = int(self.width - 30)
        
        #add start end and middle plot lines
        self.plotline1 = lineGraphic(self, self.plot_xMin,self.plot_yMin,self.plot_xMin,self.plot_yMax, QtGui.QColor(*self.alt_colour))
        self.scene.addItem(self.plotline1)
        self.plotline2 = lineGraphic(self, self.plot_xMax,self.plot_yMin,self.plot_xMax,self.plot_yMax, QtGui.QColor(*self.alt_colour))
        self.scene.addItem(self.plotline2)
        self.plotline3 = lineGraphic(self, self.plot_xMax,self.plot_yMin,self.plot_xMax,self.plot_yMax, QtGui.QColor(*self.alt_colour))
        self.scene.addItem(self.plotline3)
        self.plotline3.setVisible(False)
        
        
        self.dots = []
        self.lines = []
        
        self.startDot = Particle(self,3,[0,0])
        self.startDot.move([self.plot_xMin,self.plot_yMin])
        self.startDot.setParticleColour(*self.alt_colour)
        
        self.endDot = Particle(self,3,[0,0])
        self.endDot.move([self.plot_xMax,self.plot_yMax])
        self.endDot.setParticleColour(*self.alt_colour)
                    
        self.curveValue = 0.0
        
        self.setFocus()

        #set up timer

        self.timer = QtCore.QBasicTimer()
        self.frameCounter = 0
        
        self.GRAPHICS_RATE = 1000 / nuke.root()['fps'].value()

        #set up animating balls

        self.slidingBall_xMin = self.boxwidth + 30.0
        self.slidingBall_xMax = (self.boxwidth*2) - 30.0
        self.slidingBall_yMin = self.viewTop + 20.0
        self.slidingBall_yMax = self.boxheight - 30.0
        
        self.slidingBall = Particle(self,8,[self.slidingBall_xMin,self.slidingBall_yMin])
        self.slidingBall.setParticleColour(*self.main_colour)
    
        self.growingBall_rMin = 0.05
        self.growingBall_rMax = 1.0
        self.growingBall = Particle(self,50,[0.0,0.0])
        self.growingBall.setParticleColour(*self.main_colour)
        self.growingBall.move([self.width/6,self.viewTop + ((self.boxheight-self.viewTop)/2)])
        
        self.flashingBall_aMin = 0.0
        self.flashingBall_aMax = 255.0
        self.flashingBall = Particle(self,50,[0.0,0.0])
        self.flashingBall.setParticleColour(0.0,0.0,0.0)
        self.flashingBall.move([(self.width/6)*5,self.viewTop + ((self.boxheight-self.viewTop)/2)])

        #set up graphics text

        self.durationText = QtGuiWidgets.QGraphicsSimpleTextItem()
        if self.editMode:
            self.durationText.setText('Duration: ' + str(1 + int(self.endFrame.text()) - int(self.startFrame.text())))
        else:
            self.durationText.setText('Duration: 50')
    
        self.durationText.setPos(27,self.view.height() - 25.0)
        brush = QtGui.QBrush()
        brush.setColor( QtGui.QColor(200,255,200) )
        brush.setStyle( QtCore.Qt.SolidPattern )
        self.durationText.setBrush(brush)
        self.scene.addItem(self.durationText)
        
        self.fpsText = QtGuiWidgets.QGraphicsSimpleTextItem()
        self.fpsText.setText('FPS: ' + '%g' % nuke.root()['fps'].value())
        self.fpsText.setPos(527,self.view.height() - 25.0)
        self.fpsText.setBrush(brush)
        self.scene.addItem(self.fpsText)
        
        
        self.startText = QtGuiWidgets.QGraphicsSimpleTextItem()
        self.startText.setText('%g' % int(self.startFrame.text()))
        self.startText.setPos(self.plot_xMin-4,self.plot_yMax-20)
        self.startText.setBrush(brush)
        self.scene.addItem(self.startText)
    
        self.endText = QtGuiWidgets.QGraphicsSimpleTextItem()
        self.endText.setText('%g' % int(self.endFrame.text()))
        self.endText.setPos(self.plot_xMax-10,self.plot_yMax-20)
        self.endText.setBrush(brush)
        self.scene.addItem(self.endText)
    
        self.midText = QtGuiWidgets.QGraphicsSimpleTextItem()
        self.midText.setText('%g' % (int(self.endFrame.text())))
        self.midText.setPos((self.plot_xMax/2)+10,self.plot_yMax-20)
        self.midText.setBrush(brush)
        self.scene.addItem(self.midText)
        self.midText.setVisible(False)
    
        self.midLabelText = QtGuiWidgets.QGraphicsSimpleTextItem()
        self.midLabelText.setText('ease part')
        self.midLabelText.setPos((self.plot_xMin + 100),self.plot_yMax-20)
        self.midLabelText.setBrush(brush)
        self.scene.addItem(self.midLabelText)
        self.midLabelText.setVisible(False)
    
        #create an expression from current settings and put it in the knob
        self.setTempExpressionOnKnob()
    
    
        if self.editMode and self.animType == "wave":
            #skip the animation head and go straight to main
            self.timerState = "main"
            self.slidingBall.setParticleColour(*self.main_colour)
            self.growingBall.setParticleColour(*self.main_colour)
            self.flashingBall.setParticleColour(0.0,0.0,0.0)
            self.beginAnimations()
        else:
            #start animation head
            self.startHead()

        #plot the curve in the graphics view
        self.plotCurve()
    
        #switch to Wave view at startup by default
        if not self.editMode:
            self.waveButtonPressed()
    
        self.show()

        
    def timerEvent(self, e):

        if self.timerState == "head":
            self.timer.stop()
            self.timerState = "main"
            self.slidingBall.setParticleColour(*self.main_colour)
            self.growingBall.setParticleColour(*self.main_colour)
            self.flashingBall.setParticleColour(0.0,0.0,0.0)
            self.beginAnimations()
        
        elif self.timerState == "main":
        
            #check if finished (for ease anims only)
            if (self.frameCounter >= int(self.endFrame.text())) and (self.animType == "ease"):
                self.timer.stop()
                self.startTail()
            
            else:
                
                #get the value between 0 and 1 on the temp nuke curve
                #at this time
                try:
                    curveValue = self.getCurveValueAtTime()
                except:
                    curveValue = 0
                
                
                try:
                    #animate sliding ball
                    c = float(self.slidingBall_xMax - self.slidingBall_xMin)
                    b = float(self.slidingBall_xMin)
                    x = (curveValue * c ) + b
                    c = float(self.slidingBall_yMax - self.slidingBall_yMin)
                    b = float(self.slidingBall_yMin)
                    y = (curveValue * c ) + b
                    self.slidingBall.move([x,y])
                
                    #animate growing ball
                    c = float(self.growingBall_rMax - self.growingBall_rMin)
                    b = float(self.growingBall_rMin)
                    r = (curveValue * c ) + b
                    self.growingBall.scale(r)
                    
                    #animate flashing ball
                    c = float(self.flashingBall_aMax - self.flashingBall_aMin)
                    b = float(self.flashingBall_aMin)
                    a = (curveValue * c ) + b
                    a = min(max(a,self.flashingBall_aMin),self.flashingBall_aMax) #clamp
                    self.flashingBall.fade(a)
                        
                except:
                    pass
        
    
            self.frameCounter += 1
    

        elif self.timerState == "tail":
            
            self.startHead()
    
    
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.close()


    def startHead(self):
        #start animation head
        self.timerState = "head"
        self.slidingBall.setParticleColour(*self.alt_colour)
        self.slidingBall.move([self.slidingBall_xMin,self.slidingBall_yMin])
        self.growingBall.setParticleColour(*self.alt_colour)
        self.growingBall.scale(self.growingBall_rMin)
        self.flashingBall.setParticleColour(0.0,0.0,0.0)
        self.flashingBall.fade(self.flashingBall_aMin)
        
        self.timer.start(500, self)
                
    def startTail(self):
        #start animation tail
        self.timerState = "tail"
        self.slidingBall.move([self.slidingBall_xMax,self.slidingBall_yMax])
        self.growingBall.scale(self.growingBall_rMax)
        self.flashingBall.fade(self.flashingBall_aMax)
        
        self.timer.start(500, self)
    
    def beginAnimations(self):
        if self.timer.isActive():
            self.timer.stop()
        
        self.frameCounter = int(self.startFrameOld)
        self.duration = 1 + int(self.endFrameOld) - int(self.startFrameOld) #in fps
        self.timer.start(self.GRAPHICS_RATE, self)



    def createControlsForKnob(self):
        
        #create a new tab for this knob with all the knobs on the node in question
        theTab = nuke.Tab_Knob("anim_tab_" + self.theKnobName, self.theKnobName + " anim")
        self.theNode.addKnob(theTab)
        
        #make ease controls
        
        easeType = nuke.Text_Knob('a_easeType_display_' + self.theKnobName,'Animation type:')
        easeType.setValue('Linear')
        self.theNode.addKnob(easeType)
        
        startFrame = nuke.Int_Knob('a_startFrame_' + self.theKnobName,'Start Frame:')
        startFrame.setValue(1)
        self.theNode.addKnob(startFrame)
        
        endFrame = nuke.Int_Knob('a_endFrame_' + self.theKnobName,'End Frame:')
        endFrame.setValue(50)
        self.theNode.addKnob(endFrame)
        
        startValue = nuke.Double_Knob('a_startValue_' + self.theKnobName,'Start Value:')
        startValue.setValue(0.0)
        self.theNode.addKnob(startValue)
        
        endValue = nuke.Double_Knob('a_endValue_' + self.theKnobName,'End Value:')
        endValue.setValue(10.0)
        self.theNode.addKnob(endValue)
        
        easeTypeHidden = nuke.Text_Knob('a_easeType_' + self.theKnobName,'Ease type:')
        easeTypeHidden.setValue('Linear')
        easeTypeHidden.setVisible(False)
        self.theNode.addKnob(easeTypeHidden)
        
        #make wave controls
        
        waveType = nuke.Text_Knob('a_waveType_display_' + self.theKnobName,'Animation type:')
        waveType.setValue('Sine')
        self.theNode.addKnob(waveType)
        
        minValue = nuke.Double_Knob('a_minValue_' + self.theKnobName,'Min Value:')
        minValue.setValue(0.0)
        self.theNode.addKnob(minValue)
        
        maxValue = nuke.Double_Knob('a_maxValue_' + self.theKnobName,'Max Value:')
        maxValue.setValue(1.0)
        self.theNode.addKnob(maxValue)
        
        wavelength = nuke.Double_Knob('a_wavelength_' + self.theKnobName,'Wavelength:')
        wavelength.setValue(100.0)
        self.theNode.addKnob(wavelength)
        
        offset = nuke.Double_Knob('a_offset_' + self.theKnobName,'Offset:')
        offset.setValue(0.0)
        self.theNode.addKnob(offset)
        
        bcutoff = nuke.Double_Knob('a_bcutoff_' + self.theKnobName,'Blip cutoff:')
        bcutoff.setValue(0.95)
        self.theNode.addKnob(bcutoff)
        
        waveTypeHidden = nuke.Text_Knob('a_waveType_' + self.theKnobName,'Wave type:')
        waveTypeHidden.setValue('Sine')
        waveTypeHidden.setVisible(False)
        self.theNode.addKnob(waveTypeHidden)
        
        self.theNode.addKnob(nuke.Text_Knob('a_divider1_' + self.theKnobName,''))

        op_choice = nuke.Enumeration_Knob('a_opchoice_' + self.theKnobName,'',['Mix back','Add'])
        op_choice.setTooltip("\nAnimate the mix to turn the curve on and off.\n\nMix back: mix back to the baseline value\n(1 = curve, 0 = baseline)\n\nAdd: add the animation to the original curve.\n(1 = combined, 0 = original curve)")
        self.theNode.addKnob(op_choice)

        baseline = nuke.Double_Knob('a_baseline_' + self.theKnobName,'Baseline:')
        baseline.setValue(0.5)
        baseline.setTooltip("The value/curve to mix back to")
        self.theNode.addKnob(baseline)
        
        base_choice = nuke.Enumeration_Knob('a_basechoice_' + self.theKnobName,'',['Equilibrium','Min value', 'Max value','Orig value/curve'])
        base_choice.setTooltip("Easy presets for the baseline value")
        base_choice.clearFlag(nuke.STARTLINE)
        self.theNode.addKnob(base_choice)
        
        if self.originalValues: 
            orig_value_string = self.originalValues[self.knobIndex]
        else:
            orig_value_string = self.originalValue
        
        origValHidden = nuke.Text_Knob('a_origVal_' + self.theKnobName,'Original value')
        origValHidden.setValue(orig_value_string)
        origValHidden.setVisible(False)
        self.theNode.addKnob(origValHidden)

        knobIndexHidden = nuke.Int_Knob('a_knobIndex_' + self.theKnobName,'Knob index')
        knobIndexHidden.setValue(self.knobIndex)
        knobIndexHidden.setVisible(False)
        self.theNode.addKnob(knobIndexHidden)
        
        #put its name in the code to get value
        
        code = '''
n = nuke.thisNode()
k = nuke.thisKnob()

try:
    knob_name = k.name().split("_")[-1]
    if k.name().startswith("a_"):
        tab_knob = True
    else:
        tab_knob = False
except:
    tab_knob = False
    
if tab_knob:
    try:
        knob_index = n["a_knobIndex_%s" %knob_name].value()
        orig_val = n["a_origVal_%s" %knob_name].value()    
        
        if k.name() == ("a_basechoice_" + knob_name):
            if n['a_minValue_' + knob_name].visible():
                min_val = n['a_minValue_' + knob_name].value()
                max_val = n['a_maxValue_' + knob_name].value()
            else:
                min_val = n['a_startValue_' + knob_name].value()
                max_val = n['a_endValue_' + knob_name].value()
        
            eq = ((max_val - min_val) / 2) + min_val
                
            b = n['a_baseline_' + knob_name]
            
            if b.isAnimated():
                b.clearAnimated()
            
            if k.value() == "Equilibrium":
                b.setValue(eq)
            elif k.value() in ["Min value","Start value"]:
                b.setValue(min_val)
            elif k.value() in ["Max value","End value"]:
                b.setValue(max_val) 
            elif k.value() == "Orig value/curve":
                b.fromScript(orig_val)  
            else:
                pass
        
        elif k.name() == ("a_opchoice_" + knob_name):
            knob_parts = knob_name.split(".")
            main_knob_name = ".".join(knob_parts[:-1])
            if k.value() == "Add":
                if knob_index > -1:
                    n[main_knob_name].setExpression(n['a_exprTextAdd_' + knob_name].value(),knob_index)
                else:
                    n[knob_name].setExpression(n['a_exprTextAdd_' + knob_name].value())
                b = n['a_baseline_' + knob_name]
                if b.isAnimated():
                    b.clearAnimated()
                b.fromScript(orig_val)
                n['a_basechoice_' + knob_name].setValue('Orig value/curve')
                n['a_basechoice_' + knob_name].setEnabled(False)
                b.setEnabled(False)
            else:
                if knob_index > -1:
                    n[main_knob_name].setExpression(n['a_exprTextMult_' + knob_name].value(),knob_index)
                else:
                    n[knob_name].setExpression(n['a_exprTextMult_' + knob_name].value())
                n['a_basechoice_' + knob_name].setEnabled(True)
                n['a_baseline_' + knob_name].setEnabled(True)
                
        elif k.name() in ["a_minValue_" + knob_name, "a_maxValue_" + knob_name,"a_startValue_" + knob_name, "a_endValue_" + knob_name]:
        
            if n['a_basechoice_' + knob_name].value() == "Equilibrium":
            
                b = n['a_baseline_' + knob_name]
                if n['a_minValue_' + knob_name].visible():
                    min_val = n['a_minValue_' + knob_name].value()
                    max_val = n['a_maxValue_' + knob_name].value()
                else:
                    min_val = n['a_startValue_' + knob_name].value()
                    max_val = n['a_endValue_' + knob_name].value()        
                eq = ((max_val - min_val) / 2) + min_val
                b.setValue(eq)
    except:
        pass
        '''
        
        # self.theNode['knobChanged'].setValue(code)
        self.theNode['updateUI'].setValue(code)
        
        mixValue = nuke.Double_Knob('a_mixValue_' + self.theKnobName,'Mix:')
        mixValue.setValue(1.0)
        mixValue.setTooltip("Animate this value to turn the curve on and off")
        self.theNode.addKnob(mixValue)
        
        self.theNode.addKnob(nuke.Text_Knob('a_divider2_' + self.theKnobName,''))
        
        #add edit button, hard coded to load settings for this tab's related knob
        editButton = nuke.PyScript_Knob('a_edit_' + self.theKnobName,'EDIT')
        editButton.setValue("AnimationMaker.showWindow('%s',%s)" %(self.origKnobName,self.knobIndex))
        editButton.setTooltip("Open the interface again to edit the wave type and other options.")
        self.theNode.addKnob(editButton)
        
        #add remove button, hard coded to remove this tab and its knobs
        #'bake' expression first
        removeButton = nuke.PyScript_Knob('a_remove_' + self.theKnobName,'REMOVE')
        removeButton.setValue("AnimationMaker.remove_tab('%s','%s','%s',%s)" %(self.theNode.name(),theTab.name(),self.origKnobName,self.knobIndex))
        removeButton.setTooltip("Remove this tab and all its knobs, and create an expression using the current values.")
        removeButton.clearFlag(nuke.STARTLINE)
        self.theNode.addKnob(removeButton)

        #add restore button, hard coded to remove this tab and its knobs
        #restore original value/keyframes/expression
        restoreButton = nuke.PyScript_Knob('a_restore_' + self.theKnobName,'RESTORE')
        restoreButton.setValue("AnimationMaker.remove_tab('%s','%s','%s',%s,'%s')" %(self.theNode.name(),theTab.name(),self.origKnobName,self.knobIndex,self.originalValue))
        restoreButton.setTooltip("Remove this tab and all its knobs and restore the original value/curve.")
        restoreButton.clearFlag(nuke.STARTLINE)
        self.theNode.addKnob(restoreButton)
        
        #remove original animation from the knob
        try:
            if self.theKnob.isAnimated():
                if self.knobIndex > -1:
                    self.theKnob.clearAnimated(self.knobIndex)
                else:
                    self.theKnob.clearAnimated()
        except AttributeError:
            pass

    def closeButtonPressed(self):
        
        theNodeKnobs = self.theNode.knobs()
        
        #check if this particular node already has an animation maker tab
        #create tab and control knobs if not
        if not ("anim_tab_%s" % (self.theKnobName) in theNodeKnobs):
            self.createControlsForKnob()
        
        if self.animType == "ease" or self.animType == "waveEase":
            
            self.showEaseKnobs()
            
            #hide wave knobs if exist (for ease only)
            if self.animType == "ease":
                self.hideWaveKnobs()
            
            startValueFloat = float(self.startValue.text())
            endValueFloat = float(self.endValue.text())
            rangeFloat = endValueFloat-startValueFloat
            
            #update the existing ease knobs on the node
            self.theNode['a_startFrame_' + self.theKnobName].setValue(int(self.startFrame.text()))
            self.theNode['a_endFrame_' + self.theKnobName].setValue(int(self.endFrame.text()))
            self.theNode['a_startValue_' + self.theKnobName].setValue(startValueFloat)
            self.theNode['a_startValue_' + self.theKnobName].setRange(startValueFloat-(rangeFloat/4),endValueFloat)
            self.theNode['a_endValue_' + self.theKnobName].setValue(endValueFloat)
            self.theNode['a_endValue_' + self.theKnobName].setRange(startValueFloat , endValueFloat+(rangeFloat/4))
            self.theNode['a_easeType_' + self.theKnobName].setValue(str(self.easeType.currentText()))
            self.theNode['a_easeType_display_' + self.theKnobName].setValue("<h3><font color='yellow'>EASE </font><font color='white'>" + str(self.easeType.currentText()) + "</font></h3>")

            if self.animType == "waveEase":
                self.theNode['a_startValue_' + self.theKnobName].setVisible(False)
                self.theNode['a_endValue_' + self.theKnobName].setVisible(False)
            else:
                self.theNode['a_startValue_' + self.theKnobName].setVisible(True)
                self.theNode['a_endValue_' + self.theKnobName].setVisible(True)
                
            #update the baseline value
            self.theNode['a_baseline_' + self.theKnobName].setValue(((endValueFloat - startValueFloat) / 2)+startValueFloat)
            
            #update the basechoice dropdown
            self.theNode['a_basechoice_' + self.theKnobName].setValues(['Equilibrium','Start value', 'End value','Orig value/curve'])

                
        if self.animType == "wave" or self.animType == "waveEase":
            
            self.showWaveKnobs()
            
            #hide the ease controls if exist (for wave only)
            if self.animType == "wave":
                self.hideEaseKnobs()
                    
            minValueFloat = float(self.minValue.text())
            maxValueFloat = float(self.maxValue.text())
            wavelengthFloat = float(self.wavelength.text())
            offsetFloat = float(self.offset.text())
            bcutoffFloat = float(self.bcutoff.text())
            rangeFloat = maxValueFloat-minValueFloat
            
                
            #update the existing wave knobs on the node
            self.theNode['a_minValue_' + self.theKnobName].setValue(minValueFloat)
            self.theNode['a_minValue_' + self.theKnobName].setRange(minValueFloat-(rangeFloat/4),maxValueFloat)
            self.theNode['a_maxValue_' + self.theKnobName].setValue(maxValueFloat)
            self.theNode['a_maxValue_' + self.theKnobName].setRange(minValueFloat , maxValueFloat+(rangeFloat/4))
            
            self.theNode['a_wavelength_' + self.theKnobName].setValue(wavelengthFloat)
            self.theNode['a_wavelength_' + self.theKnobName].setRange(wavelengthFloat -(wavelengthFloat/4) , wavelengthFloat +(wavelengthFloat*4))
            self.theNode['a_offset_' + self.theKnobName].setValue(offsetFloat)
            self.theNode['a_offset_' + self.theKnobName].setRange(offsetFloat -(offsetFloat* 0.25) -10 , offsetFloat +(offsetFloat*4)+10)
            
            self.theNode['a_bcutoff_' + self.theKnobName].setValue(bcutoffFloat)
            self.theNode['a_bcutoff_' + self.theKnobName].setRange(0.0,1.0)
            if self.blip.isChecked():
                self.theNode['a_bcutoff_' + self.theKnobName].setVisible(True)
            else:
                self.theNode['a_bcutoff_' + self.theKnobName].setVisible(False)
            
            self.theNode['a_waveType_' + self.theKnobName].setValue(str(self.waveType.currentText()))
            if self.squarifyOld == True:
                self.theNode['a_waveType_display_' + self.theKnobName].setValue("<h3><font color='yellow'>WAVE </font><font color='white'>" + str(self.waveType.currentText()) + " (squared)</font></h3>")
            elif self.blipOld == True:
                self.theNode['a_waveType_display_' + self.theKnobName].setValue("<h3><font color='yellow'>WAVE </font><font color='white'>" + str(self.waveType.currentText()) + " (blip)</font></h3>")
            else:
                self.theNode['a_waveType_display_' + self.theKnobName].setValue("<h3><font color='yellow'>WAVE </font><font color='white'>" + str(self.waveType.currentText()) + "</font></h3>")
            
            #update the baseline value
            self.theNode['a_baseline_' + self.theKnobName].setValue(((maxValueFloat - minValueFloat) / 2)+minValueFloat)
            
            #update the basechoice dropdown
            self.theNode['a_basechoice_' + self.theKnobName].setValues(['Equilibrium','Min value', 'Max value','Orig value/curve'])

        #make or set the hidden animType knob
        if "a_animType_%s" % (self.theKnobName) in theNodeKnobs:
            self.theNode['a_animType_' + self.theKnobName].setValue(self.animType)
        else:
            animTypeHidden = nuke.Text_Knob('a_animType_' + self.theKnobName,'Anim type:')
            animTypeHidden.setValue(self.animType)
            animTypeHidden.setVisible(False)
            self.theNode.addKnob(animTypeHidden)


        if self.animType == "ease":
            #generate the tcl version of the expression
            self.theExpression = self.getEaseExpression(False)
        elif self.animType == "wave":
            #generate the tcl version of the expression linking to the node user knobs
            self.theExpression = self.getWaveExpression(False)
        elif self.animType == "waveEase":
            #generate the tcl version of the expression
            self.theExpression = self.getWaveEaseExpression(False)


        #make or set the hidden expressionText knobs
        if "a_exprTextAdd_%s" % (self.theKnobName) in theNodeKnobs:
            self.theNode['a_exprTextAdd_' + self.theKnobName].setValue(self.theExpression[1])
        else:
            expAddHidden = nuke.Text_Knob('a_exprTextAdd_' + self.theKnobName,'Add expression:')
            expAddHidden.setValue(self.theExpression[1])
            expAddHidden.setVisible(False)
            self.theNode.addKnob(expAddHidden)

        if "a_exprTextMult_%s" % (self.theKnobName) in theNodeKnobs:
            self.theNode['a_exprTextMult_' + self.theKnobName].setValue(self.theExpression[2])
        else:
            expMultHidden = nuke.Text_Knob('a_exprTextMult_' + self.theKnobName,'Mult expression:')
            expMultHidden.setValue(self.theExpression[2])
            expMultHidden.setVisible(False)
            self.theNode.addKnob(expMultHidden)                    
                    
        #add the tcl expression to the relevant knob
        #default to the 'mult' expression
                    
        if self.knobIndex > -1:
            self.theKnob.setExpression(self.theExpression[2],self.knobIndex)
        else:
            self.theKnob.setExpression(self.theExpression[2])


        self.updateCreateButtonPressed = True
        self.close()
        
        
    def closeEvent(self, event):
        if self.timer.isActive():
            self.timer.stop()
        
        if not self.updateCreateButtonPressed:
            #copy the original value, keyframes or expression back
            try:
                if self.theKnob.isAnimated():
                    if self.knobIndex > -1:
                        self.theKnob.clearAnimated(self.knobIndex)
                    else:
                        self.theKnob.clearAnimated()
            except AttributeError:
                pass
            
            self.theKnob.fromScript(self.originalValue)


    def easeButtonPressed(self):
        
        self.waveButton.setStyleSheet('')
        self.easeButton.setStyleSheet('QWidget { background-color: #%s }' % self.main_colour_style)
        
        if len(self.waveBoxes) > 0:
            self.hideWaveBoxes()
        
        self.showEaseBoxes()
                
        self.animType = "ease"
        self.setTempExpressionOnKnob()
        
        self.plotCurve()


    def waveButtonPressed(self):
        
        self.easeButton.setStyleSheet('')
        self.waveButton.setStyleSheet('QWidget { background-color: #%s }' % self.main_colour_style)
        
        self.hideEaseBoxes()
        if len(self.waveBoxes) > 0:
            self.showWaveBoxes()
        else:
            self.setUpWaveBoxes()
            self.showWaveBoxes()

        try:
            if self.waveEase.isChecked():
                self.animType = "waveEase"
            else:
                self.animType = "wave"
        except:
            pass

        self.setTempExpressionOnKnob()
        
        #plot the new curve
        self.plotCurve()
                
        self.timer.stop()
        self.timerState = "main"
        self.slidingBall.setParticleColour(*self.main_colour)
        self.growingBall.setParticleColour(*self.main_colour)
        self.flashingBall.setParticleColour(0.0,0.0,0.0)
        self.beginAnimations()


    def setUpEaseBoxes(self):
    
        rowSpacing = 30
        inputsLeft = 20

        #EASETYPE
        self.easeTypeLabel = QtGuiWidgets.QLabel(self)
        self.easeTypeLabel.setText('Ease Type')
        self.easeTypeLabel.move(inputsLeft, 60)
        self.easeType = QtGuiWidgets.QComboBox(self)
        self.easeType.addItems(["Linear","Quad Ease IN","Quad Ease OUT","Quad Ease IN & OUT","Expo Ease IN","Expo Ease OUT","Expo Ease IN & OUT","Ease OUT & BACK", "Ease OUT Bounce", "Ease OUT Elastic"])
        self.easeType.move(inputsLeft, self.easeTypeLabel.y()+15)
        if self.editMode:
            try:
                theIndex = self.easeType.findText(self.theNode['a_easeType_'+self.theKnobName].value(),QtCore.Qt.MatchExactly)
                self.easeType.setCurrentIndex(theIndex)
            except:
                pass
        self.easeType.currentIndexChanged.connect(self.userValuesChanged)
        self.easeTypeOld = self.easeType.currentIndex()
        self.easeBoxes.append(self.easeTypeLabel)
        self.easeBoxes.append(self.easeType)
        
        #STARTFRAME
        self.startFrameLabel = QtGuiWidgets.QLabel(self)
        self.startFrameLabel.setText('Start Frame')
        self.startFrameLabel.move(inputsLeft, self.easeType.y()+rowSpacing)
        self.startFrame = MyLineEdit(self)
        self.startFrame.move(inputsLeft, self.startFrameLabel.y()+15)
        if self.editMode:
            try:
                self.startFrame.setText(str(self.theNode['a_startFrame_'+self.theKnobName].value()))
            except:
                self.startFrame.setText('1')
        else:
            self.startFrame.setText('1')
        self.startFrame.editingFinished.connect(self.userValuesChanged)
        self.startFrameOld = self.startFrame.text()
        self.easeBoxes.append(self.startFrameLabel)
        self.easeBoxes.append(self.startFrame)
        
        #ENDFRAME
        self.endFrameLabel = QtGuiWidgets.QLabel(self)
        self.endFrameLabel.setText('End Frame')
        self.endFrameLabel.move(inputsLeft, self.startFrame.y()+rowSpacing)
        self.endFrame = MyLineEdit(self)
        self.endFrame.move(inputsLeft, self.endFrameLabel.y()+15)
        if self.editMode:
            try:
                self.endFrame.setText(str(self.theNode['a_endFrame_'+self.theKnobName].value()))
            except:
                self.endFrame.setText('50')
        else:
            self.endFrame.setText('50')
        self.endFrame.editingFinished.connect(self.userValuesChanged)
        self.endFrameOld = self.endFrame.text()
        self.easeBoxes.append(self.endFrameLabel)
        self.easeBoxes.append(self.endFrame)


        #STARTVALUE
        self.startValueLabel = QtGuiWidgets.QLabel(self)
        self.startValueLabel.setText('Start Value')
        self.startValueLabel.move(inputsLeft, self.endFrame.y()+rowSpacing+20)
        self.startValue = MyLineEdit(self)
        self.startValue.move(inputsLeft, self.startValueLabel.y()+15)
        if self.editMode:
            try:
                self.startValue.setText( '%g' % self.theNode['a_startValue_'+self.theKnobName].value()  )
            except:
                self.startValue.setText('0')
        else:
            self.startValue.setText('0')
        self.startValue.editingFinished.connect(self.userValuesChanged)
        self.startValueOld = self.startValue.text()
        self.easeBoxes.append(self.startValueLabel)
        self.easeBoxes.append(self.startValue)
        
        #ENDVALUE
        self.endValueLabel = QtGuiWidgets.QLabel(self)
        self.endValueLabel.setText('End Value')
        self.endValueLabel.move(inputsLeft, self.startValue.y()+rowSpacing)
        self.endValue = MyLineEdit(self)
        self.endValue.move(inputsLeft, self.endValueLabel.y()+15)
        if self.editMode:
            try:
                self.endValue.setText('%g' % self.theNode['a_endValue_'+self.theKnobName].value())
            except:
                self.endValue.setText('10')
        else:
            self.endValue.setText('10')
        self.endValue.editingFinished.connect(self.userValuesChanged)
        self.endValueOld = self.endValue.text()
        self.easeBoxes.append(self.endValueLabel)
        self.easeBoxes.append(self.endValue)



    def hideEaseBoxes(self):
        for e in self.easeBoxes:
            e.setVisible(False)

    def showEaseBoxes(self):
        for e in self.easeBoxes:
            e.setVisible(True)

    def hideEaseKnobs(self):
        self.theNode['a_startFrame_' + self.theKnobName].setVisible(False)
        self.theNode['a_endFrame_' + self.theKnobName].setVisible(False)
        self.theNode['a_startValue_' + self.theKnobName].setVisible(False)
        self.theNode['a_endValue_' + self.theKnobName].setVisible(False)
        self.theNode['a_easeType_' + self.theKnobName].setVisible(False)
        self.theNode['a_easeType_display_' + self.theKnobName].setVisible(False)

    def showEaseKnobs(self):
        self.theNode['a_startFrame_' + self.theKnobName].setVisible(True)
        self.theNode['a_endFrame_' + self.theKnobName].setVisible(True)
        self.theNode['a_startValue_' + self.theKnobName].setVisible(True)
        self.theNode['a_endValue_' + self.theKnobName].setVisible(True)
        self.theNode['a_easeType_display_' + self.theKnobName].setVisible(True)

    
    def setUpWaveBoxes(self):
        
        rowSpacing = 30
        inputsLeft = 20

        #WAVETYPE 
        self.waveTypeLabel = QtGuiWidgets.QLabel(self)
        self.waveTypeLabel.setText('Wave Type')
        self.waveTypeLabel.move(inputsLeft, 60)
        self.waveType = QtGuiWidgets.QComboBox(self)
        self.waveType.addItems(["Sine","Random","Noise","fBm","Turbulence","Triangle","Sawtooth","Sawtooth Curved","Sawtooth Curved Reversed","Sawtooth Exponential","Bounce"])
        self.waveType.move(inputsLeft, self.waveTypeLabel.y()+15)
        if self.editMode:
            try:
                theIndex = self.waveType.findText(self.theNode['a_waveType_'+self.theKnobName].value(),QtCore.Qt.MatchExactly)
                self.waveType.setCurrentIndex(theIndex)
            except:
                pass
                    
        self.waveType.currentIndexChanged.connect(self.userValuesChanged)
        self.waveTypeOld = self.waveType.currentIndex()
        self.waveBoxes.append(self.waveTypeLabel)
        self.waveBoxes.append(self.waveType)

        #WAVELENGTH
        self.wavelengthLabel = QtGuiWidgets.QLabel(self)
        self.wavelengthLabel.setText('Wavelength')
        self.wavelengthLabel.move(inputsLeft, self.waveType.y()+rowSpacing)
        self.wavelength = MyLineEdit(self)
        self.wavelength.move(inputsLeft, self.wavelengthLabel.y()+15)
        if self.editMode:
            try:
                self.wavelength.setText('%g' % self.theNode['a_wavelength_'+self.theKnobName].value())
            except:
                self.wavelength.setText('35')
        else:
            self.wavelength.setText('35')
        
        self.wavelength.editingFinished.connect(self.userValuesChanged)
        self.wavelengthOld = self.wavelength.text()
        self.waveBoxes.append(self.wavelengthLabel)
        self.waveBoxes.append(self.wavelength)
        
        #OFFSET
        self.offsetLabel = QtGuiWidgets.QLabel(self)
        self.offsetLabel.setText('Offset')
        self.offsetLabel.move(inputsLeft, self.wavelength.y()+rowSpacing)
        self.offset = MyLineEdit(self)
        self.offset.move(inputsLeft, self.offsetLabel.y()+15)
        if self.editMode:
            try:
                self.offset.setText('%g' % self.theNode['a_offset_'+self.theKnobName].value())
            except:
                self.offset.setText('0')
        else:
            self.offset.setText('0')
        
        self.offset.editingFinished.connect(self.userValuesChanged)
        self.offsetOld = self.offset.text()
        self.waveBoxes.append(self.offsetLabel)
        self.waveBoxes.append(self.offset)
        
        #MIN VALUE
        self.minValueLabel = QtGuiWidgets.QLabel(self)
        self.minValueLabel.setText('Min value')
        self.minValueLabel.move(inputsLeft, self.offset.y()+rowSpacing+20)
        self.minValue = MyLineEdit(self)
        
        self.minValue.move(inputsLeft, self.minValueLabel.y()+15)
        if self.editMode:
            try:
                self.minValue.setText('%g' % self.theNode['a_minValue_'+self.theKnobName].value())
            except:
                
                self.minValue.setText('0')
        else:
            self.minValue.setText('0')

        self.minValue.editingFinished.connect(self.userValuesChanged)
        self.minValueOld = self.minValue.text()
        self.waveBoxes.append(self.minValueLabel)
        self.waveBoxes.append(self.minValue)
        
        #MAX VALUE
        self.maxValueLabel = QtGuiWidgets.QLabel(self)
        self.maxValueLabel.setText('Max value')
        self.maxValueLabel.move(inputsLeft, self.minValue.y()+rowSpacing)
        self.maxValue = MyLineEdit(self)
        self.maxValue.move(inputsLeft, self.maxValueLabel.y()+15)
        if self.editMode:
            try:
                self.maxValue.setText('%g' % self.theNode['a_maxValue_'+self.theKnobName].value())
            except:
                self.maxValue.setText('1')
        else:
            self.maxValue.setText('1')

        self.maxValue.editingFinished.connect(self.userValuesChanged)
        self.maxValueOld = self.maxValue.text()
        self.waveBoxes.append(self.maxValueLabel)
        self.waveBoxes.append(self.maxValue)
        

        #RADIO BUTTONS
        self.radioGroup = QtGuiWidgets.QGroupBox(self)
        self.radioGroup.setGeometry(255, 175,200,134)
        self.waveBoxes.append(self.radioGroup)
        
        self.normalWave = QtGuiWidgets.QRadioButton('Normal wave',self.radioGroup)
        self.normalWave.move(10, 10)
        self.normalWave.setChecked(True)
        self.waveBoxes.append(self.normalWave)
        
        self.waveEase = QtGuiWidgets.QRadioButton('Combine with ease curve',self.radioGroup)
        self.waveEase.move(10, 40)
        self.waveEase.setChecked(False)
        self.waveEaseOld = False
        if self.editMode:
            try:
                if self.theNode['a_animType_'+self.theKnobName].value() == "waveEase":
                    self.waveEase.setChecked(True)
                    self.waveEaseOld = True
            except:
                pass

        self.waveEase.toggled.connect(self.userValuesChanged)
        self.waveBoxes.append(self.waveEase)
        
        self.squarify = QtGuiWidgets.QRadioButton('Squarify',self.radioGroup)
        self.squarify.move(10, 70)
        self.squarify.setChecked(False)
        self.squarifyOld = False
        if self.editMode:
            try:
                if "squared" in self.theNode['a_waveType_display_' + self.theKnobName].value():
                    self.squarify.setChecked(True)
                    self.squarifyOld = True
            except:
                pass

        self.squarify.toggled.connect(self.userValuesChanged)
        self.waveBoxes.append(self.squarify)
        
        self.blip = QtGuiWidgets.QRadioButton('Blip',self.radioGroup)
        self.blip.move(10, 100)
        self.blip.setChecked(False)
        self.blipOld = False
        if self.editMode:
            try:
                if "blip" in self.theNode['a_waveType_display_' + self.theKnobName].value():
                    self.blip.setChecked(True)
                    self.blipOld = True
            except:
                pass

        self.blip.toggled.connect(self.userValuesChanged)
        self.waveBoxes.append(self.blip)

        self.bcutoffLabel = QtGuiWidgets.QLabel(self)
        self.bcutoffLabel.setText('cutoff')
        self.bcutoffLabel.move(400, self.radioGroup.y()+102)
        self.bcutoff = MyLineEdit(self)
        self.bcutoff.setGeometry(325, self.radioGroup.y()+99, 68, 20)


        if self.editMode:
            try:
                self.bcutoff.setText('%g' % self.theNode['a_bcutoff_'+self.theKnobName].value())
            except:
                self.bcutoff.setText('0.95')
        else:
            self.bcutoff.setText('0.95')
        
        self.bcutoff.editingFinished.connect(self.userValuesChanged)
        self.bcutoffOld = self.bcutoff.text()
        self.waveBoxes.append(self.bcutoffLabel)
        self.waveBoxes.append(self.bcutoff)



    def hideWaveBoxes(self):
        for w in self.waveBoxes:
            w.setVisible(False)
    
    def showWaveBoxes(self):
        for w in self.waveBoxes:
            w.setVisible(True)

        self.bcutoffLabel.setVisible(self.blip.isChecked())
        self.bcutoff.setVisible(self.blip.isChecked())


    def hideWaveKnobs(self):
        self.theNode['a_minValue_' + self.theKnobName].setVisible(False)
        self.theNode['a_maxValue_' + self.theKnobName].setVisible(False)
        self.theNode['a_wavelength_' + self.theKnobName].setVisible(False)
        self.theNode['a_offset_' + self.theKnobName].setVisible(False)
        self.theNode['a_waveType_' + self.theKnobName].setVisible(False)
        self.theNode['a_waveType_display_' + self.theKnobName].setVisible(False)
        self.theNode['a_bcutoff_' + self.theKnobName].setVisible(False)

    def showWaveKnobs(self):
        self.theNode['a_minValue_' + self.theKnobName].setVisible(True)
        self.theNode['a_maxValue_' + self.theKnobName].setVisible(True)
        self.theNode['a_wavelength_' + self.theKnobName].setVisible(True)
        self.theNode['a_offset_' + self.theKnobName].setVisible(True)
        self.theNode['a_waveType_display_' + self.theKnobName].setVisible(True)


    def presetChanged(self):
        
        if self.presetBox.count()==1:
            self.presetBox.setItemText(0,"")
            self.presetBox.setEditable(3)
        else:
            
            if self.presetBox.currentIndex() == 0:
                self.presetBox.setItemText(0,"")
                self.presetBox.setEditable(3)
            else:
                self.presetBox.setEditable(0)
                self.presetBox.setItemText(0,"--- new ---")
    
                if self.presetBox.currentText() != self.presetBoxOld:
                    if self.presetBox.currentText() != "":
                        self.read_preset_from_file(self.presetBox.currentText())
                        self.presetBoxOld = self.presetBox.currentText()


    def reloadPreset(self):
        if self.presetBox.count() > 1 and self.presetBox.currentText() != "--- new ---":
            self.read_preset_from_file(self.presetBox.currentText())


    def userValuesChanged(self):
        
        if self.checkForChangedValues():
            
            self.duration = 1 + int(self.endFrame.text()) - int(self.startFrame.text())
            self.durationText.setText("Duration: " + str(self.duration))
            if self.animType == "wave" or self.animType == "waveEase":
                try:
                    if self.waveEase.isChecked():
                        self.animType = "waveEase"
                    else:
                        self.animType = "wave"
                except:
                    pass
            
            self.setTempExpressionOnKnob()
            
            if self.animType == "ease" or self.animType == "waveEase":
                #start animation head
                self.startHead()
            elif self.animType == "wave":
                self.timer.stop()
                self.timerState = "main"
                self.slidingBall.setParticleColour(*self.main_colour)
                self.growingBall.setParticleColour(*self.main_colour)
                self.flashingBall.setParticleColour(0.0,0.0,0.0)
                self.beginAnimations()
    
            #plot the new curve
            self.plotCurve()


    def checkForChangedValues(self):
        hasChanged = False
        
        
        if self.animType == "ease":
            
            if self.startFrame.text() != self.startFrameOld:
                self.startFrameOld = self.startFrame.text()
                hasChanged = True
            
            if self.endFrame.text() != self.endFrameOld:
                self.endFrameOld = self.endFrame.text()
                hasChanged = True
            
            if self.startValue.text() != self.startValueOld:
                self.startValueOld = self.startValue.text()
                hasChanged = True
            
            if self.endValue.text() != self.endValueOld:
                self.endValueOld = self.endValue.text()
                hasChanged = True
            
            if self.easeType.currentIndex() != self.easeTypeOld:
                self.easeTypeOld = self.easeType.currentIndex()
                hasChanged = True
        
        elif self.animType == "wave" or self.animType == "waveEase":
            
            if self.minValue.text() != self.minValueOld:
                self.minValueOld = self.minValue.text()
                hasChanged = True
            
            if self.maxValue.text() != self.maxValueOld:
                self.maxValueOld = self.maxValue.text()
                hasChanged = True
            
            if self.wavelength.text() != self.wavelengthOld:
                self.wavelengthOld = self.wavelength.text()
                hasChanged = True
            
            if self.offset.text() != self.offsetOld:
                self.offsetOld = self.offset.text()
                hasChanged = True
            
            try:
                if self.bcutoff.text() != self.bcutoffOld:
                    self.bcutoffOld = self.bcutoff.text()
                    hasChanged = True
            except:
                pass
            
            if self.waveType.currentIndex() != self.waveTypeOld:
                self.waveTypeOld = self.waveType.currentIndex()
                hasChanged = True
            
            try:
                if self.waveEase.isChecked() != self.waveEaseOld:
                    self.waveEaseOld = self.waveEase.isChecked()
                    hasChanged = True
            except:
                pass
                    
            try:
                if self.squarify.isChecked() != self.squarifyOld:
                    self.squarifyOld = self.squarify.isChecked()
                    hasChanged = True
            except:
                pass
                    
            try:
                if self.blip.isChecked() != self.blipOld:
                    self.blipOld = self.blip.isChecked()
                    if self.blipOld == True:
                        self.bcutoffLabel.setVisible(True)
                        self.bcutoff.setVisible(True)
                    else:
                        self.bcutoffLabel.setVisible(False)
                        self.bcutoff.setVisible(False)
                    
                    hasChanged = True
            except:
                pass
    
    
    
        return hasChanged


    def setTempExpressionOnKnob(self):
        
        #generate the tcl version of the expression
        if self.animType == "ease":
            self.theExpression = self.getEaseExpression(True)
        
        elif self.animType == "wave":
            self.theExpression = self.getWaveExpression(True)

        elif self.animType == "waveEase":
            self.theExpression = self.getWaveEaseExpression(True)
                
        
        #add the tcl expression to the relevant knob
        if self.knobIndex > -1 and (self.knobAmount > 1) == True:
            self.theKnob.setExpression(self.theExpression,self.knobIndex)
        else:
            self.theKnob.setExpression(self.theExpression)

                
            
    
    def plotCurve(self):
        
        index = 0
        
        c = float(self.plot_yMax - self.plot_yMin)
        b = float(self.plot_yMin)
        
    
        if len(self.dots)>0:
            dotsExist = True
        else:
            dotsExist = False


        self.plotline3.setVisible(False)
        self.midText.setVisible(False)
        self.midLabelText.setVisible(False)

        if self.animType == "ease" or self.animType == "waveEase":
            
            self.startDot.graphic.setVisible(True)
            self.endDot.graphic.setVisible(True)
            self.durationText.setVisible(True)
            
            start = float(self.startFrameOld)
            end = float(self.endFrameOld)
            
            
            if self.animType == "waveEase":
                self.startDot.move([self.plot_xMin,self.plot_yMin])
                self.endDot.move([(self.plot_xMax+self.plot_xMin)/2,self.plot_yMax])
                self.plotline3.setLine((self.plot_xMax+self.plot_xMin)/2,self.plot_yMin,(self.plot_xMax+self.plot_xMin)/2,self.plot_yMax)
                self.plotline3.setVisible(True)
                self.midText.setVisible(True)
                self.midLabelText.setVisible(True)
                self.startText.setText('%g' % int(self.startFrame.text()))
                self.midText.setText('%g' % (int(self.endFrame.text())))
                
                end += (end-start) #show more at the end of the ease
                self.endText.setText('%g' % int(end))
                
            elif self.animType == "ease":
                self.startDot.move([self.plot_xMin,self.plot_yMin])
                self.endDot.move([self.plot_xMax,self.plot_yMax])
                self.startText.setText('%g' % int(self.startFrame.text()))
                self.endText.setText('%g' % (int(self.endFrame.text())))
            
            
            curveDuration = end-start
            
            

            plotWidth = float(self.plot_xMax - self.plot_xMin)
            incAmount = curveDuration / plotWidth
            
            
            for xVal in floatRange(start,end,incAmount):
                
                try:
                    yVal = self.getCurveValueAtTime(True,xVal)
                except:
                    yVal = 0
                
                fractionAlong = ((xVal - start) / curveDuration)
                plotX = (plotWidth * fractionAlong) + self.plot_xMin
                try:
                    plotY = (yVal * c ) + b
                except:
                    plotY = 0
                            
                if not dotsExist:
                    self.dots.append(Particle(self,0.5,[0,0]))
                
                self.dots[index].setParticleColour(*self.main_colour)
                self.dots[index].move([plotX,plotY])
                
                if self.animType == "waveEase":
                    #colour ease part differently
                    if xVal <= (curveDuration/2)+0.5:
                        self.dots[index].setParticleColour(*self.alt_colour)
                
                
                #add line joining this one to the last dot
                if index>0:
                    if not dotsExist:
                        theLine = lineGraphic(self,plotX,plotY,self.dots[index-1].pos[0],self.dots[index-1].pos[1],QtGui.QColor(*self.main_colour))
                        self.lines.append(theLine)
                        self.scene.addItem(theLine)
                    else:
                        self.lines[index-1].setLine(plotX,plotY,self.dots[index-1].pos[0],self.dots[index-1].pos[1])
                                    
                index +=1

        elif self.animType == "wave":
            
            self.startDot.graphic.setVisible(False)
            self.endDot.graphic.setVisible(False)
            self.durationText.setVisible(False)
            self.startText.setText('%g' % int(self.plot_xMin-30))
            self.endText.setText('%g' % (int(self.plot_xMax-29)))
            
            for plotX in range(self.plot_xMin,self.plot_xMax+1):
                try:
                    plotY = self.getCurveValueAtTime(True,plotX - self.plot_xMin)
                except:
                    plotY = 0
                
                try:
                    plotY = (plotY * c ) + b
                except:
                    plotY = 0
                    
                if not dotsExist:
                    self.dots.append(Particle(self,0.5,[0,0]))


                self.dots[index].setParticleColour(*self.main_colour)
                self.dots[index].move([plotX,plotY])

                #add line joining this one to the last dot
                if index>0:
                    if not dotsExist:
                        theLine = lineGraphic(self,plotX,plotY,self.dots[index-1].pos[0],self.dots[index-1].pos[1],QtGui.QColor(*self.main_colour))
                        self.lines.append(theLine)
                        self.scene.addItem(theLine)
                    else:
                        self.lines[index-1].setLine(plotX,plotY,self.dots[index-1].pos[0],self.dots[index-1].pos[1])

                index +=1


    def getCurveValueAtTime(self,plot = None,plotTime = 0):
        
        if plot:
            t = float(plotTime)
        else:
            t = self.frameCounter
            
        #get the value at current time from the expression on the node itself
        try:
            curveValue = self.theNode[self.theKnobName].getValueAt(t)
        except:
            try:
                if self.knobIndex > -1:
                    curveValue = self.theKnob.getValueAt(t,self.knobIndex)
                else:
                    curveValue = self.theKnob.getValueAt(t,0)
            except:
                curveValue = 0

        return curveValue
        
        


    def getEaseExpression(self,forPanel = False):
        
        theEaseType = str(self.easeType.currentText())
        
        if forPanel == True:
            #generate a normalized nuke expression from which to read the curve values
            #when animating things in the panel
            
            c = "1"
            b = "0"
            
            t = "(frame - %s)" % (self.startFrameOld)
            d = "(%s - %s)" % (self.endFrameOld,self.startFrameOld)
            
           
            td = "(%s / %s)" % (t,d)
            td2 = "(%s / (%s / 2))" % (t,d)
        
            easePrefix = "frame < %s ? 0 : frame > %s ? 1 : " % (self.startFrameOld,self.endFrameOld)
                
                
        else:
        
            #generate nuke expression based on the values chosen
            
            if self.animType == "waveEase":
                c = "1"
                b = "0"
                easePrefix = "frame < a_startFrame_%s ? 0 : frame > a_endFrame_%s ? 1 : " % (self.theKnobName,self.theKnobName)
            else:
                easePrefix = "frame < a_startFrame_%s ? a_startValue_%s : frame > a_endFrame_%s ? a_endValue_%s : " % (self.theKnobName,self.theKnobName,self.theKnobName,self.theKnobName)
                c = "(a_endValue_%s - a_startValue_%s)" % (self.theKnobName,self.theKnobName)
                b = "a_startValue_%s" % (self.theKnobName)
                
            t = "(frame - a_startFrame_%s)" % (self.theKnobName)
            d = "(a_endFrame_%s - a_startFrame_%s)" % (self.theKnobName,self.theKnobName)
            td = "((frame - a_startFrame_%s) / (a_endFrame_%s - a_startFrame_%s))" % (self.theKnobName,self.theKnobName,self.theKnobName)
            td2 = "((frame - a_startFrame_%s) / ((a_endFrame_%s - a_startFrame_%s) / 2))" % (self.theKnobName,self.theKnobName,self.theKnobName)
        
            mix = "a_mixValue_%s" % (self.theKnobName)
            baseline = "a_baseline_%s" % (self.theKnobName)
                
                
        if theEaseType == "Linear":
            #c * t / d + b
            theExpression = easePrefix + "%s * %s / %s + %s" %(c,t,d,b)
        
        elif theEaseType == "Quad Ease IN":
            #c * td * td + b
            theExpression = easePrefix + "%s * %s * %s + %s" %(c,td,td,b)
        
        elif theEaseType == "Quad Ease OUT":
            #-c * td * (td-2) + b
            theExpression = easePrefix + "-%s * %s * (%s-2) + %s" %(c,td,td,b)
        
        elif theEaseType == "Quad Ease IN & OUT":
            #(td2 < 1 ? c/2*td2*td2 + b : -c/2 * ((td2-1)*((td2-1)-2) - 1) + b)
            theExpression = easePrefix + "(%s < 1 ? %s/2 * %s * %s + %s : -%s/2 * ((%s-1)*((%s-1)-2) - 1) + %s)" %(td2,c,td2,td2,b,c,td2,td2,b)

        elif theEaseType == "Expo Ease IN":
            #c * (2 ** (10 * (td - 1)) ) + b
            theExpression = easePrefix + "%s * (2 ** (10 * (%s - 1)) ) + %s" %(c,td,b)

        elif theEaseType == "Expo Ease OUT":
            #c * ( -( 2**(-10 * t/d) ) + 1 ) + b
            theExpression = easePrefix + "%s * ( -( 2**(-10 * %s) ) + 1 ) + %s" %(c,td,b)

        elif theEaseType == "Expo Ease IN & OUT":
            #td2 < 1 ? c / 2 * (2 ** (10 * (td2 - 1)) ) + b : c / 2 * (-(2 ** (-10 * (td2-1))) + 2) + b
            theExpression = easePrefix + "%s < 1 ? %s / 2 * (2 ** (10 * (%s - 1)) ) + %s : %s / 2 * (-(2 ** (-10 * (%s-1))) + 2) + %s" %(td2,c,td2,b,c,td2,b)

        elif theEaseType == "Ease OUT & BACK":
            #s = 1.70158
            #c * ((t/d-1)*(t/d-1)*((s+1)*(t/d-1) + s) + 1) + b
            theExpression = easePrefix + "%s * ((%s/%s-1)*(%s/%s-1)*((%s+1)*(%s/%s-1) + %s) + 1) + %s" %(c,t,d,t,d,1.70158,t,d,1.70158,b)

        elif theEaseType == "Ease OUT Bounce":
            #td < (1/2.75) ? c * (7.5625 * td * td) + b : td < (2/2.75) ? c * (7.5625 * (td - (1.5/2.75)) * (td - (1.5/2.75)) + 0.75) + b :        td < (2.5/2.75) ? c * (7.5625 * (td - (2.25/2.75)) * (td - (2.25/2.75)) + 0.9375) + b : c * (7.5625 * (td - (2.625/2.75)) * (td - (2.625/2.75)) + 0.984375) + b

            theExpression = easePrefix + "%s < (1/2.75) ? %s * (7.5625 * %s * %s) + %s : %s < (2/2.75) ? %s * (7.5625 * (%s - (1.5/2.75)) * (%s - (1.5/2.75)) + 0.75) + %s :        %s < (2.5/2.75) ? %s * (7.5625 * (%s - (2.25/2.75)) * (%s - (2.25/2.75)) + 0.9375) + %s : %s * (7.5625 * (%s - (2.625/2.75)) * (%s - (2.625/2.75)) + 0.984375) + %s" %(td,c,td,td,b,td,c,td,td,b,td,c,td,td,b,c,td,td,b)


        elif theEaseType == "Ease OUT Elastic":
            
            #c * (2**(-10 * td)) * sin( (td * d-((d * 0.3) / 4)) * (3.14159 * 2) / (d * 0.3) ) + c + b
            theExpression = easePrefix + "%s * (2**(-10 * %s)) * sin( (%s * %s-((%s * 0.3) / 4)) * (3.14159 * 2) / (%s * 0.3) ) + %s + %s" %(c,td,td,d,d,d,c,b)

        if forPanel == False:
            #add to the original value/curve, by mix amount
            addExpression = "%s + ((%s) * %s)" %(baseline,theExpression,mix)
            #mix back with baseline value by the mix amount
            multExpression = "(((%s) - %s) * %s) + %s" %(theExpression,baseline,mix,baseline)
            #combine all into a list (the first may be used in a WaveEase expression)
            theExpression = [theExpression,addExpression,multExpression]

        return theExpression


    def getWaveExpression(self, forPanel = False, easeExpression = None):
        
        #generate nuke expression based on the values chosen
        
        theWaveType = str(self.waveType.currentText())
        theExpression = ""
        
        if forPanel == True:
            #generate a normalized nuke expression from which to read the curve values
            #when animating things in the panel
            
            c = "1"
            b = "0"
            
            try:
                w = str(max(float(self.wavelength.text()),1.0))
            except:
                w = "1"
            
            try:
                o = str(float(self.offset.text()))
            except:
                o = "0"

            try:
                cutoff = str(max(float(self.bcutoff.text()),0.6))
            except:
                cutoff = "0.95"

        else:
            #generate the final expression to put into nuke
            c = "(a_maxValue_%s - a_minValue_%s)" % (self.theKnobName,self.theKnobName)
            b = "a_minValue_%s" % (self.theKnobName)
            w = "a_wavelength_%s" % (self.theKnobName)
            o = "a_offset_%s" % (self.theKnobName)
            mix = "a_mixValue_%s" % (self.theKnobName)
            baseline = "a_baseline_%s" % (self.theKnobName)


        
        if theWaveType == "Sine":
            #(((sin(((frame*((pi * 2)/(w/2))/2) + o))+1)/2) * c ) + b
            theExpression = "((sin(((frame*((pi * 2)/(%s/2))/2) + %s))+1)/2)" %(w,o)
        
        
        elif theWaveType == "Random":
            #((random((frame/(waveLength/2))+offset)) * (maxVal-minVal) ) + minVal
            theExpression = "(random((frame/(%s/2))+%s))" %(w,o)

        elif theWaveType == "Noise":
            #(((1*(noise((frame/waveLength)+offset))+1 ) /2 ) * (maxVal-minVal) ) + minVal
            theExpression = "((1*(noise((frame/%s)+%s))+1 ) /2 )" %(w,o)

        elif theWaveType == "fBm":
            #min(max(((fBm((frame/50), 0, 0,10,2,0.5)*0.75)+0.5),0),1)
            #min(max(((fBm((frame/waveLength)+offset, 0, 0,10,2,0.5)*0.75)+0.5),0),1)
            #(((1*(fBm((frame/waveLength)+offset),10,2,0.5)+1 ) /2 ) * (maxVal-minVal) ) + minVal
            theExpression = "min(max(((fBm((frame/%s)+%s, 0, 0,10,2,0.5)*0.75)+0.5),0),1)" %(w,o)

        elif theWaveType == "Turbulence":
            #(((1*(turbulence((frame/waveLength)+offset),10,2,0.5)+1 ) /2 ) * (maxVal-minVal) ) + minVal
            #max(min((turbulence((frame/5), 0, 0,10,2,0.5)*(1+1/3)),1),0)
            #max(min((turbulence((frame/wavelength)+offset, 0, 0,10,2,0.5)*(1+1/3)),1),0)
            theExpression = "max(min((turbulence((frame/%s)+%s, 0, 0,10,2,0.5)*(1+1/3)),1),0)" %(w,o)

        elif theWaveType == "Triangle":
            #(((((2*asin(sin(2*pi*(frame/waveLength)+offset)))/pi) / 2)+0.5) * (maxVal-minVal) ) + minVal
            theExpression = "((((2*asin(sin(2*pi*(frame/%s)+%s)))/pi) / 2)+0.5)" %(w,o)

        elif theWaveType == "Sawtooth":
            #((1/waveLength)*(((frame-1)+offset) % waveLength) * (maxVal-minVal) ) + minVal
            theExpression = "(1/"+w+")*(((frame-1)+"+o+") % "+w+")"

        elif theWaveType == "Sawtooth Curved":
            #((sin((1/(pi/2))*(((frame-1)+offset)/(waveLength/2.46666666)) % (pi/2)))>0.99999? 1 : (sin((1/(pi/2))*(((frame-1)+offset)/(waveLength/2.46666666)) % (pi/2))) * (maxVal-minVal) ) + minVal
            theExpression = "(sin((1/(pi/2))*(((frame-1)+"+o+")/("+w+"/2.46666666)) % (pi/2)))>0.99999? 1 : (sin((1/(pi/2))*(((frame-1)+"+o+")/("+w+"/2.46666666)) % (pi/2)))"

        elif theWaveType == "Sawtooth Curved Reversed":
            #((cos((1/(pi/2))*(((frame-1)+offset)/(waveLength/2.46666666)) % (pi/2)))>0.99999? 1 : (cos((1/(pi/2))*(((frame-1)+offset)/(waveLength/2.46666666)) % (pi/2))) * (maxVal-minVal) ) + minVal
            theExpression = "(cos((1/(pi/2))*(((frame-1)+"+o+")/("+w+"/2.46666666)) % (pi/2)))>0.99999? 1 : (cos((1/(pi/2))*(((frame-1)+"+o+")/("+w+"/2.46666666)) % (pi/2)))"

        elif theWaveType == "Sawtooth Exponential":
            #((((((exp((1/(pi/2))*(((frame-1)+offset)/(waveLength/4.934802)) % pi*2)))/534.5)) - 0.00186741)>0.999987? 1 : (((((exp((1/(pi/2))*(((frame-1)+offset)/(waveLength/4.934802)) % pi*2)))/534.5)) - 0.00186741) * (maxVal-minVal) ) + minVal
            theExpression = "(((((exp((1/(pi/2))*(((frame-1)+"+o+")/("+w+"/4.934802)) % pi*2)))/534.5)) - 0.00186741)>0.999987? 1 : (((((exp((1/(pi/2))*(((frame-1)+"+o+")/("+w+"/4.934802)) % pi*2)))/534.5)) - 0.00186741)"
        
        elif theWaveType == "Bounce":
            #((sin(((frame/waveLength)*pi)+offset)>0?sin(((frame/waveLength)*pi)+offset):cos((((frame/waveLength)*pi)+offset)+(pi/2))) * (maxVal-minVal) ) + minVal
            theExpression = "(sin(((frame/%s)*pi)+%s)>0?sin(((frame/%s)*pi)+%s):cos((((frame/%s)*pi)+%s)+(pi/2)))" %(w,o,w,o,w,o)


        #add the ease expression if there is one
        if easeExpression:
            if type(easeExpression) is list:
                easeExpression = easeExpression[0]
            theExpression = "(%s) * (%s)" %(theExpression,easeExpression)
            
        #then set max and min
        theExpression = "((%s) * %s) + %s" %(theExpression, c, b)


        #SQUARIFY
        if self.squarifyOld == True:
            if forPanel:
                c05 = "0.5"
                theMax = "1"
                theMin = "0"
            else:
                c05 = "(((a_maxValue_%s - a_minValue_%s)/2)+a_minValue_%s)" % (self.theKnobName,self.theKnobName,self.theKnobName)
                theMax = "a_maxValue_%s" % (self.theKnobName)
                theMin = "a_minValue_%s" % (self.theKnobName)
            
            
            theExpression = "(%s) > %s ? %s : %s" %(theExpression,c05,theMax,theMin)

        #BLIPPIFY
        if self.blipOld == True:
            if forPanel:
                theMax = "1"
                theMin = "0"
            else:
                theMax = "a_maxValue_%s" % (self.theKnobName)
                theMin = "a_minValue_%s" % (self.theKnobName)
                cutoff = "(a_bcutoff_%s * (%s - %s)) + %s" % (self.theKnobName,theMax,theMin,theMin)
                
                
            theExpression = "(%s) > %s ? %s : %s" %(theExpression,cutoff,theMax,theMin)


        if forPanel == False:
            #add to the original value/curve, by mix amount
            addExpression = "%s + ((%s) * %s)" %(baseline,theExpression,mix)
            #mix back with baseline value by the mix amount
            multExpression = "(((%s) - %s) * %s) + %s" %(theExpression,baseline,mix,baseline)
            #combine both into a tuple
            theExpression = [theExpression,addExpression,multExpression]

        return theExpression
            

    def getWaveEaseExpression(self,forPanel):

        easeExpression = self.getEaseExpression(forPanel)
        return self.getWaveExpression(forPanel,easeExpression)



    def save_preset_to_file(self):
        if self.presetBox.currentText() == "":
            self.presetBox.setItemText(self.presetBox.currentIndex(),"--- new ---")
            self.presetBox.keyPressEvent(QtGui.QKeyEvent(QtCore.QEvent.KeyPress, QtCore.Qt.Key_Enter, QtCore.Qt.NoModifier))    
            self.presetBox.setEditable(0)
        
        #get preset name from box
        preset_name = str(self.presetBox.currentText())
        
        if preset_name in ["--- new ---", ""]:
            return None
        
        #make dictionary from current values
        save_values = {}
        save_values['startFrame'] = str(self.startFrame.text())
        save_values['endFrame'] = str(self.endFrame.text())
        save_values['startValue'] = str(self.startValue.text())
        save_values['endValue'] = str(self.endValue.text())
        save_values['easeType'] = str(self.easeType.currentIndex())
        save_values['minValue'] = str(self.minValue.text())
        save_values['maxValue'] = str(self.maxValue.text())
        save_values['waveLength'] = str(self.wavelength.text())
        save_values['offset'] = str(self.offset.text())
        save_values['bcutoff'] = str(self.bcutoff.text())
        save_values['waveType'] = str(self.waveType.currentIndex())
        save_values['normalWave'] = self.normalWave.isChecked()
        save_values['waveEase'] = self.waveEase.isChecked()
        save_values['squarify'] = self.squarify.isChecked()
        save_values['blip'] = self.blip.isChecked()
        save_values['animType'] = self.animType
        
        
        #save to file
        success = save_preset(preset_name,save_values)
        if success:
            msgBox = QtGuiWidgets.QMessageBox()
            msgBox.setWindowTitle("AnimationMaker")
            msgBox.setStyleSheet('QWidget { background-color: #%s }' %self.bg_colour_style)
            msgBox.setText("<h3>'%s' preset saved</h3>" %preset_name)
            msgBox.exec_()        

    def delete_preset_from_file(self):
        
        #get preset name from box
        preset_name = str(self.presetBox.currentText())
        
        if preset_name in ["--- new ---", ""]:
            return None
            
        self.presetBox.removeItem(self.presetBox.currentIndex())
        
        #save to file, but in delete mode
        success = save_preset(preset_name,None,True)
        if success:
            msgBox = QtGuiWidgets.QMessageBox()
            msgBox.setWindowTitle("AnimationMaker")
            msgBox.setStyleSheet('QWidget { background-color: #%s }' %self.bg_colour_style)
            msgBox.setText("<h3>'%s' preset deleted</h3>" %preset_name)
            msgBox.exec_()

        #get preset name from box
        preset_name = str(self.presetBox.currentText())
        
        if preset_name == "":
            self.presetBox.setEditable(0)
            self.presetBox.setItemText(0,"--- new ---")


    def read_preset_from_file(self,preset_name):
        #read preset from file
        read_values = read_preset(preset_name)
        
        if read_values:
            #set the values
            self.startFrame.setText(read_values['startFrame'])
            self.endFrame.setText(read_values['endFrame'])
            self.startValue.setText(read_values['startValue'])
            self.endValue.setText(read_values['endValue'])
            self.easeType.setCurrentIndex(int(read_values['easeType']))
            self.minValue.setText(read_values['minValue'])
            self.maxValue.setText(read_values['maxValue'])
            self.wavelength.setText(read_values['waveLength'])
            self.offset.setText(read_values['offset'])
            self.bcutoff.setText(read_values['bcutoff'])
            self.waveType.setCurrentIndex(int(read_values['waveType']))
            self.normalWave.setChecked(read_values['normalWave'])
            self.waveEase.setChecked(read_values['waveEase'])
            self.squarify.setChecked(read_values['squarify'])
            self.blip.setChecked(read_values['blip'])
            
            if read_values['animType']=="ease":
                #switch to Ease view
                self.easeButtonPressed()
            else:
                #switch to Wave view
                self.waveButtonPressed()


def floatRange(start, stop, step):
    assert step > 0.0
    total = start
    compo = 0.0
    while total <= stop:
        yield total
        y = step - compo
        temp = total + y
        compo = (temp - total) - y
        total = temp
    

#################################
#        PARTICLE CLASS         #
#################################

class Particle():
    
    # Initialise
    
    def __init__(self, graphicsWindow, rad, pos):
        
        self.pos = pos
        self.radius = rad
        self.updateCount = 0
        
        
        #-------------------graphics----------------------
        #get reference to main window
        self.graphicsWindow = graphicsWindow
        
        #make small circle shape
        self.graphic = QtGuiWidgets.QGraphicsEllipseItem(0,0,self.radius*2,self.radius*2)
        
        #no border
        pen = QtGui.QPen()
        pen.setStyle(QtCore.Qt.NoPen)
        self.graphic.setPen(pen)
        
        self.setParticleColour(0,0,0)
        
        #set transform origin to centre of ball
        self.graphic.setTransformOriginPoint(QtCore.QPointF(self.radius, self.radius))
        try:
            self.graphic.setAcceptsHoverEvents(False)
        except:
            #PySide2
            self.graphic.setAcceptHoverEvents(False)
        self.graphic.setZValue(10) #always on top
        
        #add this to the scene
        self.graphicsWindow.scene.addItem(self.graphic)
    
    
    def move(self,newPos):
        
        #update position
        self.pos = newPos
        gPosX = self.pos[0] - self.radius
        gPosY = self.pos[1] - self.radius
        self.graphic.setPos( gPosX, gPosY )
    
    def scale(self,factor):
        
        #update scale factor
        self.graphic.setScale(factor)

    def fade(self,factor):
        
        self.setParticleColour(factor,factor,factor)
    
    def setParticleColour(self,r,g,b):
        
        #filled with chosen colour
        brush = QtGui.QBrush()
        brush.setColor( QtGui.QColor(r,g,b) )
        brush.setStyle( QtCore.Qt.SolidPattern )
        self.graphic.setBrush(brush)




class lineGraphic(QtGuiWidgets.QGraphicsLineItem):
    
    def __init__(self, parent, x1,y1,x2,y2,colour):
        
        QtGuiWidgets.QGraphicsLineItem.__init__(self,x1,y1,x2,y2)
        
        self.points = [[float(x1),float(y1)],[float(x2),float(y2)]]
        
        lineWidth = 2
        
        pen = QtGui.QPen()
        pen.setColor( colour )
        pen.setWidth(lineWidth)
        self.setPen(pen)
        
        drop_colour = QtGui.QColor(255,255,255,255)
        
        drop = QtGuiWidgets.QGraphicsDropShadowEffect(parent)
        drop.setColor(colour)
        drop.setOffset(0)
        drop.setBlurRadius(lineWidth*15)
        
        self.setGraphicsEffect(drop)



def toScriptMultiple(val_string):
    #takes a toScript() style string and returns
    #the separate parts (eg scripts for x,y,z) as a list of strings
            
    vals = []
    val = ""
    in_braces = False
    in_number = False
    index = 0
    for c in val_string:
        index += 1
    
        if c == "}" and in_braces:
            val += c
            vals.append(val)
            val = ""
            in_braces = False
    
        if c == "{" or in_braces:
            val += c
            in_braces = True
            continue
    
        if c == " " and not in_braces:
            in_number = False
            if val:
                vals.append(val)
            val = ""
            continue
    
        if c in ['0','1','2','3','4','5','6','7','8','9','.','-']:
            val += c
            in_number = True
    
        if index == len(val_string):
            vals.append(val)
    
    vals = [v for v in vals if v!=""]
    
    return vals





def remove_tab(node_name,tab_name,knob_name,knob_index,orig_value = None):
    node = nuke.toNode(node_name)
    in_user_tab = False
    to_remove = []
    for n in range(node.numKnobs()):
        cur_knob = node.knob(n)
        is_tab = isinstance(cur_knob, nuke.Tab_Knob)
    
        # Track is-in-tab state
        if is_tab and cur_knob.name() == tab_name: # Tab name to remove
            in_user_tab = True
        elif is_tab and in_user_tab:
            in_user_tab = False
        
        # Collect up knobs to remove later
        if in_user_tab:
            to_remove.append(cur_knob)
    

    if orig_value:
        #copy the original value, keyframes or expression
        #back to the knob
        try:
            if node[knob_name].isAnimated():
                if knob_index > -1:
                    node[knob_name].clearAnimated(knob_index)
                else:
                    node[knob_name].clearAnimated()
        except AttributeError:
            pass
        
        if knob_index > -1:
            #more difficult: need to keep the other values the same
        
            #get script of current values/curve/expressions in the knob
            knob_script = node[knob_name].toScript()
            #split those into separate strings
            current_values = toScriptMultiple(knob_script)
            #split the original stored script separate strings
            orig_values = toScriptMultiple(orig_value)
            #create a new list, starting with the current state of the knob
            new_values = current_values
            #replace one of the items with the original (knob index in question)
            new_values[knob_index] = orig_values[knob_index]
            #join them into a space separated string (script)
            new_values_string = " ".join(new_values)
            new_values_string = new_values_string.strip()
            #replace all values in the knob with the new script
            #effectively only changing the one in question
            node[knob_name].fromScript(new_values_string)
        else:
            node[knob_name].fromScript(orig_value)
    else:
        #create a baked version of the expression
        #and put it in the original knob
        
        bake_values = []
        has_keyframes = False
        
        for k in reversed(to_remove):
            if k.Class() not in ["PyScript_Knob","Tab_Knob","Text_Knob"]:
                if k.isAnimated():
                    if k.hasExpression():
                        bake_values.append( (k.name(),"(%s)"%k.animation(0).expression()) )
                    else:
                        has_keyframes = True
                        break
                else:
                    bake_values.append( (k.name(),k.value()) )
                    
        if has_keyframes:
            #can't make an expression as there's keyframes on one of the knobs
            #(probably baseline) so bake a keyframe on every frame
            #give them a warning first
            if not nuke.ask("There are keyframes involved in creating this curve, so it must be baked if you want to remove the tab. Continue?"):
                return None
            
            ret = nuke.getFramesAndViews( "Bake frames?", '%s-%s' % (nuke.root().firstFrame(), nuke.root().lastFrame()) )
            if not ret:
                return None
                
            fRange = nuke.FrameRange( ret[0] )
            views = ret[1]
            
            curves = []
            for v in views:
                curves.extend( node[knob_name].animations( v ) )

            for curve in curves:
                for f in range(fRange.first(), fRange.last()):
                    curve.setKey( f, curve.evaluate( f ) )
                curve.setExpression( 'curve' )
                            
        else:
            #create a new combined expression using current tab values
            
            if knob_index > -1:
                bake_exp = node[knob_name].animation(knob_index).expression()
            else:
                bake_exp = node[knob_name].animation(0).expression()
            
            for bv in bake_values:
                bake_exp = bake_exp.replace(bv[0],str(bv[1]))
            
            if knob_index > -1:
                node[knob_name].setExpression(bake_exp,knob_index)
            else:
                node[knob_name].setExpression(bake_exp)

    # Remove in reverse order so tab is empty before removing Tab_Knob
    for k in reversed(to_remove):
        node.removeKnob(k)
    
    # Select first tab
    node.knob(0).setFlag(0)
    
    #on linux, fix bug where tab appears twice 
    fixRemoveKnobs(node)
    
    #delete single
    node['updateUI'].setValue(None)

def _showPanel(node):
    time.sleep(0.5)
    nuke.executeInMainThread(node.showControlPanel, ())

def fixRemoveKnobs(node):
    node.hideControlPanel()
    thread.start_new_thread(_showPanel, (node,))
    
    
class MyLineEdit(QtGuiWidgets.QLineEdit):
    def __init__(self, parent=None):
        super(MyLineEdit, self).__init__(parent)
        self.parent = parent

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Up:
            try:
                self.setText(str(int(self.text()) + 1))
            except:
                self.setText(str(float(self.text()) + 0.01))
            finally:
                pass
        elif event.key() == QtCore.Qt.Key_Down:
            try:
                self.setText(str(int(self.text()) - 1))
            except:
                self.setText(str(float(self.text()) - 0.01))
            finally:
                pass
        QtGuiWidgets.QLineEdit.keyPressEvent(self, event)
    
    def keyReleaseEvent(self, event):
        #update the animations for certain values, but only if up and down released
        if self in [self.parent.wavelength,self.parent.offset,self.parent.startFrame,self.parent.endFrame]:
            if event.key() in [QtCore.Qt.Key_Up,QtCore.Qt.Key_Down]:
                self.parent.userValuesChanged()
        event.accept()


class MyComboBox(QtGuiWidgets.QComboBox):
    def __init__(self, parent=None):
        super(MyComboBox, self).__init__(parent)
        self.parent = parent

    def keyPressEvent(self, event):
        if event.key() in [QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return]:
            self.parent.save_preset_to_file()
        QtGuiWidgets.QComboBox.keyPressEvent(self, event)
    


def get_preset_path():
    try:
        #put it in the same path as this module
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "AnimationMaker_presets.xml")
        return filepath
    except:
        return None


def save_preset(preset_name, new_settings, delete=False):
    preset_name = preset_name.replace(" ","_-sp-_") #space
    preset_name = preset_name.replace("'","_-sq-_") #single quote
    preset_name = preset_name.replace('"',"_-dq-_") #double quote

    filepath = get_preset_path()

    #return None if can't get path
    if not filepath:
        print "AnimationMaker: Couldn't get the preset path"
        return None
    
    root_element = None
    preset_element = None

    #if file exists, get root and preset elements    
    if os.path.exists(filepath):

        #read in the whole tree
        root_element = parse_file(filepath)
        
        #Get this preset's element
        try:
            preset_element = root_element.find(preset_name)
        except:
            preset_element = None

    #create root element if haven't got it already
    if root_element is None:
        #create root xml element
        root_element = xml.Element('PRESETS')

    if delete:
        #remove the preset element
        if preset_element is not None:
            root_element.remove(preset_element)
    else:
        #create preset element if haven't got it already
        if preset_element is None:
            preset_element = xml.Element(preset_name)
            root_element.append(preset_element)
            
        #get keys from new_settings dict
        try:
            settings_keys = new_settings.keys()
        except:
            #something wrong with the dict passed to this function
            print "AnimationMaker: Preset dictionary not valid"
            return None
            
        #build the settings tree for this preset
        for key in settings_keys:
            #Get this setting's element
            try:
                setting_element = preset_element.find(key)
            except:
                setting_element = None
                
            #make one if it doesn't exist
            if setting_element is None:
                setting_element = xml.Element(key)
                preset_element.append(setting_element)
    
            #set the value of the setting
            setting_element.text = str(new_settings[key])

    #instead of writing the normal way
    #create a formatted string and write that
    try:
        rough_string = xml.tostring(root_element, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        formatted_string = reparsed.toprettyxml(indent="\t")
        
        f = open(filepath,'w')
        f.write(formatted_string)
        f.close()
        
        #tell parent function it was successful
        return True
    
    except:
        print "AnimationMaker: Failed to write XML tree to presets file"
        return None


def read_preset(preset_name):
        
    preset_name = preset_name.replace(" ","_-sp-_") #space
    preset_name = preset_name.replace("'","_-sq-_") #single quote
    preset_name = preset_name.replace('"',"_-dq-_") #double quote

    filepath = get_preset_path()

    #return None if can't get path or doesn't exist
    if filepath == None:
        return None
    if not os.path.exists(filepath):
        return None

    #read in the whole tree
    root_element = parse_file(filepath)
        
    #Get this tool's element
    try:
        preset_element = root_element.find(preset_name)
    except:
        preset_element = None

    #return if this preset isn't found in the file
    if preset_element is None:
        return None

    #create dict of settings for this preset and return it
    settings_data = {}

    for setting_element in preset_element:
        key, value = setting_element.tag, setting_element.text

        #convert boolean values
        if value == 'True':
            value = True
        elif value == 'False':
            value = False
        elif value[0]=="[" and value[-1]=="]":
            #this is a list so turn it into one
            value = ast.literal_eval(value)
        
        settings_data[key] = value
        
    return settings_data


def read_preset_list():
    filepath = get_preset_path()

    #return None if can't get path or doesn't exist
    if filepath == None:
        return None
    if not os.path.exists(filepath):
        return None

    #read in the whole tree
    root_element = parse_file(filepath)
    preset_list = []
    for child in root_element:
        preset = child.tag.replace("_-sp-_"," ")
        preset = preset.replace("_-sq-_","'")
        preset = preset.replace("_-dq-_",'"')
        preset_list.append(preset)
    
    return preset_list

    

def parse_file(filepath):
    #custom parser to read nicely formatted XML
    #reads in line by line and strips out tabs/spaces
    try:
        f = open(filepath,'r')
        filestring = ''.join([line.strip() for line in f.readlines()])
        f.close()
        file_tree = xml.fromstring(filestring)
        return file_tree
    except:
        return None