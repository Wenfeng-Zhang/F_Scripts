#-*- coding:utf8 -*-
#__author__ = 'wenfeng zhang'
#https://github.com/Wenfeng-Zhang

'''
from node_timer import *
toolbar = nuke.menu("Nodes")
m = toolbar.addMenu('F Script',)
m.addCommand('Node timer',
             'node_timer()',
             'shift+t')
'''

import nuke
try:
    from PySide import QtCore,QtGui
except:
    from PySide2 import QtCore
    from PySide2 import QtWidgets as QtGui

class MyWidget(QtGui.QWidget):
    def __init__(self,node,knobValue):
        super(self.__class__, self).__init__()
        
        self.node = node
        
        self.my_timer = QtCore.QTimer()

        layout = QtGui.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)

        layout2 = QtGui.QHBoxLayout()
        layout2.setAlignment(QtCore.Qt.AlignTop)

        layout3 = QtGui.QVBoxLayout()
        layout3.setAlignment(QtCore.Qt.AlignTop)

        #开始按钮
        self.btn1 = QtGui.QPushButton('Start')
        self.btn1.clicked.connect(self.btn1Clicked)
        
        #结束按钮
        self.btn2 = QtGui.QPushButton('Stop')
        self.btn2.clicked.connect(self.btn2Clicked)

        #速率调节盘
        self.dial = QtGui.QDial()
        self.dial.setFocusPolicy(QtCore.Qt.NoFocus)
        self.dial.setMinimum(10)
        self.dial.setMaximum(200)
        self.dial.setProperty("Value", knobValue)   #默认显示为100
        self.dial.setNotchesVisible(True)           #显示调节盘刻度
        self.dial.valueChanged.connect(self.dialValueChanged)

        #######################################
        self.dial.valueChanged.connect(self.updateValue)
        #######################################
        
        #速率文字
        self.label = QtGui.QLabel()
        self.label.setObjectName("label")
        self.label.setText("Swich interval(s)")

        #速率实时显示
        self.label_2 = QtGui.QLabel()
        self.label_2.setObjectName("label_2")
        self.label_2.setText(str(float(self.dial.value())/100.0))

        #将按钮添加到排列中
        layout.addWidget(self.btn1)
        layout.addWidget(self.btn2)
        layout2.addWidget(self.dial)
        layout3.addWidget(self.label_2)
        layout3.addWidget(self.label)

        #合并排列
        master_layout = QtGui.QHBoxLayout()
        master_layout.addLayout(layout)
        master_layout.addLayout(layout2)
        master_layout.addLayout(layout3)
        self.setLayout(master_layout)

        #信号槽
        self.my_timer.timeout.connect(self.btn1Clicked)

    #结束按钮
    def btn2Clicked(self):
        self.my_timer.stop()
        self.btn1.setEnabled(True)

    #速率值
    def dialValueChanged(self):
        self.label_2.setText(str(float(self.dial.value())/100.0))
        return float(self.dial.value()/100.0)

    #伴随速率变化而变化
    def btn1Clicked(self):
        if 'which' in self.node.knobs():
            knobn = 'which'
        elif 'mix' in self.node.knobs():
            knobn = 'mix'
        def update_process(self):
            cur_val = self.node[knobn].value()
            if cur_val < 1:
                self.node[knobn].setValue(1)
            elif cur_val > 0:
                self.node[knobn].setValue(0)
            print(cur_val)
        update_process(self)
        self.my_timer.start(1000*self.dialValueChanged())
        self.btn1.setEnabled(False)

    def makeUI(self):
        return self

    def updateValue(self):
        self.node['MyWidget'].setValue("MyWidget(nuke.thisNode(),%s)"%(self.dial.value()))

def node_timer():
    node = nuke.selectedNode()
    if [knobname for knobname in node.allKnobs() if knobname.name()=='mix' or knobname.name()=='which']:
        if node.knob('User2'):
            pass
        else:
            knob_tk = nuke.Tab_Knob('User2','Timer')
            node.addKnob(knob_tk)
        if node.knob('MyWidget'):
            pass
        else:
            knob = nuke.PyCustom_Knob("MyWidget", "", "MyWidget(nuke.thisNode(),%s)"%(100) )
            node.addKnob(knob)
        if node.knob('Notes'):
            pass
        else:
            knob_tk2 = nuke.Text_Knob('Notes','Info:')
            knob_tk2.setValue("Adjust the knob to change the switching frequency")
            node.addKnob(knob_tk2)
    else:
        nuke.message('This node does not have a "mix" button.')

if __name__ == '__main__':
    node_timer()