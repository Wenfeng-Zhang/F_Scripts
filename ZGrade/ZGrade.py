#-*- coding:utf8 -*-
#__author__ = 'wenfeng zhang'
#https://github.com/Wenfeng-Zhang

'''
import ZGrade
toolbar = nuke.menu("Nodes")
m = toolbar.addMenu('F Script',)
m.addCommand('ZGrade','ZGrade.main()',icon="Clamp.png")
'''


import nukescripts,nuke

class ZGrade_Panel(nukescripts.PythonPanel):
    def __init__(self):
        nukescripts.PythonPanel.__init__(self, 'ZGrade')
    
        layer_list = ["depth","depth_extra","rgba"]
        self.layers = nuke.Enumeration_Knob("layer","Layers",layer_list)
        self.addKnob(self.layers)
        
        
        self.channels_ = ['red','green','blue','alpha']
        
        self.channel_list = nuke.Enumeration_Knob("channel","",self.channels_)
        self.channel_list.clearFlag(nuke.STARTLINE)
        self.channel_list.setVisible(False)
        self.addKnob(self.channel_list)
        


        self._viewers = {}
        for n in nuke.allNodes("Viewer", nuke.Root()):
            self._viewers[n.name()] = n
        self._specialRanges = ["input", "global", "custom"]
        
    

        self._rangeEnum = nuke.Enumeration_Knob("frame_range", "Frame range", self._specialRanges + self._viewers.keys())
        self.addKnob(self._rangeEnum)
        


        self._frameRange = nuke.String_Knob('frame_range_sting', "", str(nuke.root().frameRange()))
        self._frameRange.clearFlag(nuke.STARTLINE)
        if self._rangeEnum.value() == "custom":
            self._frameRange.setValue(str(nuke.root().frameRange()))
        else:
            self._setFrameRangeFromSource(self._rangeEnum.value())
        self.addKnob(self._frameRange)

        
        self.depth_clamp = nuke.String_Knob('number,"inf"or"nan"', 'Depth clamp','1000000')
        self.addKnob(self.depth_clamp)
        
        self.warning = nuke.Text_Knob('waring', '<span style="color:red">Not Numbers</span>')
        self.warning.clearFlag(nuke.STARTLINE)
        self.warning.setVisible(False)
        self.addKnob(self.warning)
        

        self.channels_name = ''
        self.channel_names()
        
        self.channel_num = 1
        
        
        self.frameranges = ''
        self.firstframe = ''
        self.lastframe = ''
        self.frame_ranges()
        
        
        self.depth_clamp_value = self.depth_clamp.value()

        self.warning_bool = True
        self.mark = False

    def knobChanged(self, knob):
        
        if (knob == self.layers) or (knob == self.channel_list):
            if self.layers.getValue() != 0:
                if self.layers.getValue() == 1:
                    channel_extra = self.channels_[:]
                    channel_extra.pop()
                    self.channel_list.setValues(channel_extra)
                else:
                    self.channel_list.setValues(self.channels_)
                    
                self.channel_list.setVisible(True)
                self.channel_num = self.channel_list.getValue()
            else:
                self.channel_list.setVisible(False)
                
            self.channel_names()
            
            
        if (knob == self._frameRange):
            self._rangeEnum.setValue("custom")
            self.frame_ranges()
            self.frameranges = self._frameRange.value().strip()
            
        if (knob == self._rangeEnum):
            self._setFrameRangeFromSource(knob.value())
            self.frame_ranges()
            self.frameranges = self._frameRange.value().strip()
            
        if (knob == self.depth_clamp):
            value = self.depth_clamp.value().strip()
            if not value.replace(".",'').isdigit() and value not in ("nan","inf") or value[-1] == '.' or value[0] == '.' or value.count('.')>1:
                self.warning.setVisible(True)
                self.warning_bool = False
            else:
                self.warning.setVisible(False)
                self.warning_bool = True
            self.depth_clamp_value = self.depth_clamp.value().strip()
            


    def _setFrameRangeFromSource(self, source):
        if (source == "input"):
            try:
                activeInput = nuke.activeViewer().activeInput()
                self._frameRange.setValue(str(nuke.activeViewer().node().upstreamFrameRange(activeInput)))
            except:
                self._frameRange.setValue(str(nuke.root().frameRange()))
                
        elif (source == "global"):
            self._frameRange.setValue(str(nuke.root().frameRange()))
            
        elif (source == "custom"):
            self._frameRange.setValue(str(self._frameRange.value()))
                
        else:
            self._frameRangeFromViewer(source)



    def _frameRangeFromViewer( self, viewer ):

        viewerRange = str(self._viewers[viewer].playbackRange())
        self._frameRange.setValue(viewerRange)
            


    def channel_names(self):
        # channel_dict = {'depth_extra':{'red':'red','green':'green','blue':'blue','alpha':'a'},
                        # 'rgba':{'red':'red','green':'green','blue':'blue','alpha':'a'},
                       # }
        
        if self.layers.value() == 'depth':
            self.channels_name = 'depth.Z'
        else:
            self.channels_name = '%s.%s'%(self.layers.value(), self.channel_list.value())#channel_dict[self.layers.value()][self.channel_list.value()])



    def frame_ranges(self):
        
        frames = self._frameRange.value()
        
        if '-' in frames.strip():
            self.firstframe = int(frames.strip().split('-')[0])
            self.lastframe = int(frames.strip().split('-')[1])
        
        else:
            self.firstframe = self.lastframe = int(frames.strip())


    
            
    def show(self):
        result = nukescripts.PythonPanel.showModalDialog(self)
        if result:
            self.mark = True
            

            print self.channels_name
            print self.firstframe
            print self.lastframe
            print self.depth_clamp_value


#ZGrade_Panel().show()



class Calculate_data(ZGrade_Panel):
    def __init__(self,node):
        super(Calculate_data,self).__init__()
        self.node = node
        self.show()
        
        self.channel_ = self.channels_name
        self.selectlayer = self.channels_name.split('.')[0]
        
        if self.selectlayer in nuke.layers(self.node):
            self.layer_bool = True
        else:
            self.layer_bool = False
        
        
        
        self.Min_value = ''
        self.Min_value_frame = ''
        
        
        self.Max_value = ''
        self.Max_value_frame = ''
        

       
        self.e1 = '%s==0?inf:%s'%(self.channel_, self.channel_)
        self.e2 = '%s>nan||%s<%s?%s:0'%(self.channel_, self.channel_, self.depth_clamp_value, self.channel_)
        
        
        self.Expression2 = ''
        


    def getMinMax(self):
        try:
            Expression1 = nuke.nodes.Expression(channel0 = self.channels_name, expr0 = self.e1, inputs = [self.node])
            Expression2 = nuke.nodes.Expression(channel0 = self.channels_name, expr0 = self.e2, inputs = [self.node])
            MinColor = nuke.nodes.MinColor(channels=self.channels_name, target=0, inputs=[Expression1])
            Inv = nuke.nodes.Invert(channels=self.channels_name, inputs=[Expression2])
            MaxColor = nuke.nodes.MinColor(channels=self.channels_name, target=0, inputs=[Inv])
        

            nuke.execute( MinColor, self.firstframe, self.lastframe )
            
            Min_value_list = []
            for i in xrange(self.firstframe, self.lastframe+1):
                minV = -MinColor['pixeldelta'].valueAt(i)
                Min_value_list.append(minV)
            self.Min_value = min(Min_value_list)
            self.Min_value_frame = Min_value_list.index(self.Min_value)+self.firstframe



            nuke.execute( MaxColor, self.firstframe, self.lastframe )
            
            Max_value_list = []
            for i in xrange(self.firstframe, self.lastframe+1):
                maxV = MaxColor['pixeldelta'].valueAt(i)+1
                Max_value_list.append(maxV)
            self.Max_value = max(Max_value_list)
            self.Max_value_frame = Max_value_list.index(self.Max_value) + self.firstframe
        except:
            for n in (Expression1, Expression2, MinColor, MaxColor, Inv ):
                nuke.delete( n )

        for n in (Expression1, MinColor, MaxColor, Inv ):
            nuke.delete( n )
        
        self.Expression2 = Expression2


        
    def create_Nodes(self):
        
        text = '%s: %s\n%s:%s %s:%s'%('Frame Range',self.frameranges,'MaxF',self.Max_value_frame,'MinF',self.Min_value_frame)
        
        grade = nuke.nodes.Grade(channels=self.channels_name, blackpoint=self.Min_value, whitepoint=self.Max_value, name='ZGrade', tile_color = '336860415', note_font_color = '4278239231', label=text)
        grade.setInput(0, self.Expression2)
        self.Expression2['note_font_color'].setValue(4278239231)
        
        
        if self.layers.getValue() != 0:
        
            node_colors = [4278190335,16711935,65535,4278124287][int(self.channel_num)]
            node_colors_text = [4278190335,16711935,8388607,4278124287][int(self.channel_num)]
            
            self.Expression2['note_font_color'].setValue(node_colors_text)
            grade['note_font_color'].setValue(node_colors_text)
            num = self.channel_num + 1
            shuffle = nuke.nodes.Shuffle(name='ZShuffle',red=num,green=num,blue=num,alpha=num,tile_color = str(node_colors),ypos=grade.ypos()+20)
            shuffle.setInput(0,grade)
            shuffle['in'].setValue(self.channels_name)

    def run(self):
        if self.mark:
            if self.warning_bool and self.layer_bool:
                self.getMinMax()
                self.create_Nodes()
                
            elif not self.layer_bool:
                nuke.message('There is no "%s" layer.'%(self.selectlayer))
                reload(main())
  
            elif not self.warning_bool:
                nuke.message('"Depth clamp" can only be numbers or "nan" or "inf".')
                reload(main())


def main():
    try:
        node = nuke.selectedNode()
        obj = Calculate_data(node)
        obj.run()
    except:
        pass
if __name__ == "__main__":
    main()