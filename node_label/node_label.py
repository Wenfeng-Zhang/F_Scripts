#-*- coding:utf8 -*-
#__author__ = 'wenfeng zhang'
#https://github.com/Wenfeng-Zhang

#menu.py
#import node_label

import nuke

channel = '[if {[value this.channels]=="rgb"} {return "([value channels])\n"}] [if {[value this.channels]=="rgba"} {return "([value channels])\n"}]'
OFlow2_label = 'Method:[value this.interpolation]\n[if {[value this.timing2]=="Input Speed"} {return "Input Speed:[value this.timingInputSpeed]"}][if {[value this.timing2]=="Output Speed"} {return "Output Speed:[value this.timingOutputSpeed]"}][if {[value this.timing2]=="Frame"} {return "Frame:[value this.timingFrame2]"}]'
Transform_label = '<font color =#548DD4> T :<font color = red>[value this.translate.x]|[value this.translate.y] </font><font color =#548DD4> R :<font color = red>[expr int([value this.rotate])] </font><font color =#548DD4> S :<font color = red>[value this.scale.w]|[value this.scale.h]</font>'

labels = {  #Image
            'Write'        :   channel,
            'Read'         :   '<font size="3" color =#548DD4><b> Frame range :</b></font> <font color = red>[value first] - [value last] </font>',
            
            #Time
            'TimeOffset'   :   'offset:[value this.time_offset]\n[if {[value this.reverse_input]==true} {return reverse}]',
            'Retime'       :   'input:[knob this.input.first]->[knob this.input.last]\noutput:[knob this.output.first]->[knob this.output.last]',
            'FrameRange'   :   '[knob this.first_frame]->[knob this.last_frame]',
            'FrameBlend'   :   'Num frame:[value numframes]',
            'AppendClip'   :   'First Frame:[knob this.firstFrame]',
            'OFlow2'       :   OFlow2_label,
            
            #Channel
            'ChannelMerge' :   'mix: [value mix]',
            'Remove'       :   channel,
            'ShuffleCopy'  :   '[value in]->[value out]',
            'Shuffle'      :   '[value in]',
            
            #color
            'Clamp'        :   channel+'[if {[value this.minimum]!=0} {return "minimum:[value this.minimum]\n"}][if {[value this.maximum]!=0} {return "maximum:[value this.maximum]\n"}]',
            'Multiply'     :   channel+"value:[value value]",
            'Invert'       :   channel,
            'Saturation'   :   'S: [value saturation]',
            'Toe2'         :   'lift: [value this.lift]',
            'HueShift'     :   'hue rotation: [value this.hue_rotation]',
            'Colorspace'   :   'in:[value this.colorspace_in]\nout:[value this.colorspace_out]',
            'Grade'        :   channel,
            
            #Filter
            'Blur'         :   channel+'Size:[value size]',
            'Defocus'      :   channel+'defocus: [value defocus]',
            'EdgeBlur'     :   'size: [value size]',
            'Dilate'       :   channel+'size: [value size]',
            'FilterErode'  :   channel+'size: [value size]',
            'Erode'        :   channel+'size: [value size]',
            'Glow2'        :   channel+'size: [value size]',
            'Glow'         :   channel+'size: [value size]',
            'Laplacian'    :   channel+'size: [value this.size]',
            'MotionBlur'   :   'Samples: [value this.shutterSamples]',
            'MotionBlur2D' :   'shutter: [value this.shutter]',
            'Sharpen'      :   channel+'shutter: [value this.size]',
            'VectorBlur2'  :   'motion: [value this.scale]',
            'VectorBlur'   :   channel+'multiply: [value this.scale]',
            
            #Keyer
            'Difference'   :   'gain: [value this.gain]',
            
            #Merge
            'Merge'        :   'mix: [value mix]',
            'Keymix'       :   channel+'mix: [value mix]',
            'Dissolve'     :   channel+'which: [value which]',
            'Switch'       :   'which: [value which]',
            'Premult'      :   channel,
            'Unpremult'    :   channel,
            
            #Transform
            'Mirror'       :   '[if {[value this.Horizontal]==true} {return "Horizontal "}][if {[value this.Vertical]==true} {return " Vertical"}]',
            'Mirror2'      :   '[if {[value this.flip]==true} {return "vertical "}][if {[value this.flop]==true} {return " horizontal"}]',
            'Tracker4'     :   '[value transform] | frame:[value reference_frame]',
            'VectorDistort':   'frame:[value this.reference_frame]',
            'STMap'        :   channel,
            'Transform'    :   Transform_label,
         
         
}

for knobName,label in labels.items():
    nuke.knobDefault('%s.label'%knobName,label)



