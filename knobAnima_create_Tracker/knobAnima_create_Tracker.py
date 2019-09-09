#-*- coding:utf8 -*-
#__author__ = 'wenfeng zhang'
#https://github.com/Wenfeng-Zhang

'''
import knobAnima_create_Tracker
m = nuke.menu('Animation')
m.addSeparator()
m.addCommand('Create Tracker', 'knobAnima_create_Tracker.main()',icon='Tracker.png')
'''

import nuke
import re

#re,用于提取按钮的动画tcl脚本
REGEXP_script = '{curve .+?}'
#re,用于从tcl脚本中提取动画设置的初始值
REGEXP_frame = '(x)(\d+)?'
#用于起效的按钮
Knob_list = ['BBox_Knob', 'XY_Knob']

#################################################
class KnobAnimation_create_trackers():
    def __init__(self,knob):
        self.knob = knob
        self.RUN_ = False

        if self.knob.Class() not in Knob_list:
            nuke.message('Button type error')
            return None

        if self.knob.hasExpression() or not self.knob.isAnimated():
            nuke.message('Buttons have expressions or no animation')
            return None

        self.RUN_ = True

#根据按钮创建动画的tcl脚本
    def create_animated_list(self,knob):
        script = knob.toScript()

        if self.knob.Class() == 'XY_Knob':
            lists = [script]
            return lists

        elif self.knob.Class() == 'BBox_Knob':
            m = re.findall(REGEXP_script, script)
            curve_1 = '%s %s' % (m[0],m[1])
            curve_2 = '%s %s' % (m[0],m[3])
            curve_3 = '%s %s' % (m[2],m[3])
            curve_4 = '%s %s' % (m[2],m[1])
            
            lists = [curve_1,curve_2,curve_3,curve_4]
            return lists

#根据动画的tcl脚本创建Tracker节点的TCL跟踪脚本
    def create_trackers_scripts(self,knob_animated_list, trs=False):
        all_trackers = []
        
        if trs:
            trs_val = "1 1 1"
        else:
            trs_val = "1 0 0"
            
        counter = 1
        frame_list_re = re.compile(REGEXP_frame)
        for curves in knob_animated_list:
            name = "tracker{0}".format(counter)
            frame_list = frame_list_re.findall(curves)
            frame_start_x = frame_list[0][-1]
            frame_start_y = frame_list[1][-1]
            
            tracker_str = ''' { {curve K x%s 1} "%s" %s 
                                {curve K x%s 0} {curve K x%s 0} %s {curve x%s 0} 
                                1 0 -15 -15 15 15 -10 -10 10 10 {} {}  {}  {}  {}  {}  {}  {}  {}  {}  {}   }''' % (frame_start_x, name, curves, frame_start_x, frame_start_y, trs_val, frame_start_x)

            all_trackers.append(tracker_str)
            counter+=1
        
        all_trackers_str = "{ \n%s\n}" % ("\n".join(all_trackers))
        
        from_script_str = """
                            { 1 31 %s } 
                            { { 5 1 20 enable e 1 } 
                            { 3 1 75 name name 1 } 
                            { 2 1 58 track_x track_x 1 } 
                            { 2 1 58 track_y track_y 1 } 
                            { 2 1 63 offset_x offset_x 1 } 
                            { 2 1 63 offset_y offset_y 1 } 
                            { 4 1 27 T T 1 } 
                            { 4 1 27 R R 1 } 
                            { 4 1 27 S S 1 } 
                            { 2 0 45 error error 1 } 
                            { 1 1 0 error_min error_min 1 } 
                            { 1 1 0 error_max error_max 1 } 
                            { 1 1 0 pattern_x pattern_x 1 } 
                            { 1 1 0 pattern_y pattern_y 1 } 
                            { 1 1 0 pattern_r pattern_r 1 } 
                            { 1 1 0 pattern_t pattern_t 1 } 
                            { 1 1 0 search_x search_x 1 } 
                            { 1 1 0 search_y search_y 1 } 
                            { 1 1 0 search_r search_r 1 } 
                            { 1 1 0 search_t search_t 1 } 
                            { 2 1 0 key_track key_track 1 } 
                            { 2 1 0 key_search_x key_search_x 1 } 
                            { 2 1 0 key_search_y key_search_y 1 } 
                            { 2 1 0 key_search_r key_search_r 1 } 
                            { 2 1 0 key_search_t key_search_t 1 } 
                            { 2 1 0 key_track_x key_track_x 1 } 
                            { 2 1 0 key_track_y key_track_y 1 } 
                            { 2 1 0 key_track_r key_track_r 1 } 
                            { 2 1 0 key_track_t key_track_t 1 } 
                            { 2 1 0 key_centre_offset_x key_centre_offset_x 1 } 
                            { 2 1 0 key_centre_offset_y key_centre_offset_y 1 } 
                            } 
                            %s
                                """ % (len(knob_animated_list), all_trackers_str)
        
        return from_script_str.strip()

#创建Tracker节点（此处为Tracker4），将生成的TCL跟踪脚本传入。
    def create_trackerNode(self,node,scripts):
        x = node.xpos()
        y = node.ypos()
        w = node.screenWidth()
        h = node.screenHeight()
        m = int(x + w/2)
        
        tracker = nuke.createNode("Tracker4",inpanel=False)
        tracker.setName(node.name()+'_'+'Tracker')
        tracker.setInput(0,None)
        tracker.setXYpos(int(m+w), int(y+w/2))
        tracks = tracker["tracks"]
        tracks.fromScript(scripts)
        
    def run(self):
        if self.RUN_:
            trackers_scripts = self.create_trackers_scripts(self.create_animated_list(self.knob))
            self.create_trackerNode(self.knob.node(), trackers_scripts)
            
def main():
    knob = nuke.thisKnob()
    func = KnobAnimation_create_trackers(knob)
    func.run()
        
        
        
        
        
            