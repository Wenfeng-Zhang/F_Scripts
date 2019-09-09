#-*- coding:utf8 -*-
#__author__ = 'wenfeng zhang'
#https://github.com/Wenfeng-Zhang

# import knob_Curve
# m = nuke.menu('Animation')
# m.addSeparator()
# m.addCommand('Knob_Curve', 'knob_Curve.main()',)


import nuke
import re

class Curve_Panel(object):
    def __init__(self,knob):
        self.first_frame = str(int(nuke.root()['first_frame'].getValue()))
        self.list_frame = str(int(nuke.root()['last_frame'].getValue()))

        self.list_chann = ''
        self.channlist = ''
        self.outchannlist = ''

        self.knob = knob
        self.firstframe = ''
        self.lastframe = ''
        self.from_channel_num = ''
        self.output_channel_num = ''
        self.max_value = ''
        self.min_value = ''

        self.channel_name_list()

    #当前按钮的可调节通道名字列表
    def channel_name_list(self):
        knobarray = self.knob.arraySize()
        
        if self.knob.label():
            label = self.knob.label()
        else:
            label = self.knob.name()
            
        #按钮名加通道名‘name.channel’
        self.list_chann = []
        if knobarray == 1:
            self.channlist = re.escape(label)
            self.outchannlist = self.channlist
            self.list_chann.append(label)
        #如果当前按钮不是只能计算一个通道的类型，那么在输出的通道栏增加一个All
        else:
            self.list_chann_view = []
            for i in xrange(knobarray):
                names = self.knob.names(i)
                chann = '%s.%s'%(label, names)
                self.list_chann.append(chann)
                self.list_chann_view.append(re.escape(chann))
            self.channlist = ' '.join(self.list_chann_view)
            self.outchannlist = '%s %s' % ('All',self.channlist)

    #对话框
    def Panel(self):    
        p = nuke.Panel('Curve Custom')
        
        p.addEnumerationPulldown('From channel', self.channlist)
        p.addEnumerationPulldown('Output channel', self.outchannlist)
        p.addSingleLineInput('FrameRange', '%s-%s'%(self.first_frame,self.list_frame))
        p.addSingleLineInput('Max', '1')
        p.addSingleLineInput('Min', '0')
        

        if p.show():
            from_channel = str(p.value('From channel'))
            out_channel = str(p.value('Output channel'))
            self.max_value = float(p.value('Max'))
            self.min_value = float(p.value('Min'))

            
            #from通道的数字
            self.from_channel_num = self.list_chann.index(from_channel)
            

            #output通道的数字
            if out_channel == 'All':
                self.output_channel_num = out_channel
                
            else:
                self.output_channel_num = self.list_chann.index(out_channel)
            
 
                    
            curve_frame = p.value('FrameRange')
            
            if '-' in curve_frame.strip():
                self.firstframe = int(curve_frame.strip().split('-')[0])
                self.lastframe = int(curve_frame.strip().split('-')[1])
                
            else:
                self.firstframe = self.lastframe = int(curve_frame.strip())
                            

class knob_Curve(Curve_Panel):
    def __init__(self,knob):
    #def __init__(self,knob,firstframe,lastframe,from_channel_num,output_channel_num,max_value,min_value):
        super(knob_Curve,self).__init__(knob)
        self.knob = knob
        self.Panel()
        
        '''
        self.firstframe = firstframe
        self.lastframe = lastframe
        self.from_channel_num = from_channel_num
        self.output_channel_num = output_channel_num
        self.max_value = max_value
        self.min_value = min_value
        '''
        
        
    #所有选中通道的值列表
    def Value_list(self):
        value_frame = [self.knob.valueAt(i,self.from_channel_num) for i in xrange(self.firstframe, self.lastframe+1)]
        return value_frame
    
    #曲线的最大值
    def Value_max(self):
        return max(self.Value_list())
        
    #曲线的最小值
    def Value_min(self):
        return min(self.Value_list())


    #区间比值
    def Interval_multiple(self):
        return (self.max_value - self.min_value)/(self.Value_max()-self.Value_min())
        

    #新计算完毕的区间函数
    def Custom_max_min(self,index=0):
    
        curve = self.knob.animation(index).expression()
        curve = ''.join(curve.split(' '))
        curve_name = "(%s-%s)*%s+%s"%(curve,str(self.Value_min()),str(self.Interval_multiple()),str(self.min_value))
        print curve_name
        return curve_name
    
    def Set_value_in_knob(self):
    
        knob_channel_num = self.knob.arraySize()
        
        #如果按钮调节数为1，此类型按钮则直接烘焙
        if knob_channel_num == 1:
            self.knob.setExpression(self.Custom_max_min())
            nuke.animation(self.knob.fullyQualifiedName(), "generate", (str(self.firstframe),str(self.lastframe), "1", "y", self.knob.fullyQualifiedName()))

        #如果按钮调节数为多个，则分别检测用户的选择
        else:
            
            #选中的输入通道label
            curve = '%s.%s'%(self.knob.name(),str(self.from_channel_num))
            #如果选中了ALL，则迭代全部烘焙
            if self.output_channel_num == 'All':
            
                self.knob.setExpression(self.Custom_max_min(self.from_channel_num),self.from_channel_num)
                nuke.animation('%s.%s'%(self.knob.fullyQualifiedName(),str(self.from_channel_num)), "generate", (str(self.firstframe),str(self.lastframe), "1", "y", self.knob.name()))
                
                for i in xrange(knob_channel_num):
                    if i != self.from_channel_num:
                        self.knob.setExpression(curve,i)
                    nuke.animation('%s.%s'%(self.knob.fullyQualifiedName(),str(i)), "generate", (str(self.firstframe),str(self.lastframe), "1", "y", self.knob.name()))
                self.knob.setSingleValue(True)
                
            #选中要输出的就单独烘焙某个通道
            else:
                #如果输入和输出相同
                if self.output_channel_num == self.from_channel_num:
                    self.knob.setExpression(self.Custom_max_min(self.from_channel_num),self.from_channel_num)
                else:
                    curve = "(%s-%s)*%s+%s"%(curve,str(self.Value_min()),str(self.Interval_multiple()),str(self.min_value))
                    self.knob.setExpression(curve,self.output_channel_num)
                nuke.animation('%s.%s'%(self.knob.fullyQualifiedName(),str(self.output_channel_num)), "generate", (str(self.firstframe),str(self.lastframe), "1", "y", self.knob.name()))


def main():
    knob = nuke.thisKnob()
    try:
        obj = knob_Curve(knob)
        obj.Set_value_in_knob()
    except:
        pass
        
# def main():
    # knob = nuke.thisKnob()
    # obj = knob_Curve(knob)
    # obj.Set_value_in_knob()

    
if __name__ == "__main__":
    main()
        
