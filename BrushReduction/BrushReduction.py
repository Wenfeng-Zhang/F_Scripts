#-----------------------------
#By Mads Hagbarth Damsbo 2017
#-----------------------------

import math
import threading
import nuke

class DPAlgorithm():
    #not sure who the author of this is!?
    def distance(self,  a, b):
        return  math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)

    def point_line_distance(self,  point, start, end):
        if (start == end):
            return self.distance(point, start)
        else:
            n = abs(
                (end[0] - start[0]) * (start[1] - point[1]) - (start[0] - point[0]) * (end[1] - start[1])
            )
            d = math.sqrt(
                (end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2
            )
            return n / d

    def rdp(self, points, epsilon):
        """
        Reduces a series of points to a simplified version that loses detail, but
        maintains the general shape of the series.
        """
        dmax = 0.0
        index = 0
        i=1
        for i in range(1, len(points) - 1):
            d = self.point_line_distance(points[i], points[0], points[-1])
            if d > dmax :
                index = i
                dmax = d

        if dmax >= epsilon :
            results = self.rdp(points[:index+1], epsilon)[:-1] + self.rdp(points[index:], epsilon)
        else:
            results = [points[0], points[-1]]
        return results


def reduce_selected_brush_stroke(withDefaults=False):
    #------------------------
    #       SETTINGS
    #------------------------
    epsilon     = 10                    #Your threshold
    frame       = nuke.frame()          #The frame to reference...
    rpNode      = nuke.selectedNode()   #The node to process
    makeCopy    = False                 #Since nuke.Undo is broken, we want to make a backup

    if not withDefaults:
        #Make a little fancy menu
        p = nuke.Panel('Reduce Brush Strokes :: Settings')
        p.addSingleLineInput('Epsilon', '10')
        p.addBooleanCheckBox('Make Copy of Node?', False)
        ret = p.show()
        epsilon = float(p.value('Epsilon'))
        makeCopy =  p.value('Make Copy')

    if makeCopy: #Make a copy of the selected node.
        originalNode = rpNode
        nuke.nodeCopy('%clipboard%')
        nuke.nodePaste('%clipboard%')
        rpNode =  nuke.selectedNode()
        rpNode.setInput(0,originalNode.input(0))

    solver = DPAlgorithm() #The algorithm object
    cKnob= rpNode['curves']
    selectedShapes = cKnob.getSelected()
    task = nuke.ProgressTask('Reducing Roto...')
    task.setProgress(0)  
    for i,shape in enumerate(selectedShapes) :
        thisShape = [] 
        alen = float(len(selectedShapes))                       #Used to calculate progress

        # try:         
        for x,p in enumerate(shape) :                       #Get a list of all the points in the roto shape
            tempPosition = p.center.getPosition(frame)
            thisShape.append([tempPosition[0],tempPosition[1],x])

        reducedShape = solver.rdp(thisShape,epsilon)        #Magic happens here.. reduce the shape  

        for x,p in reversed( list( enumerate( shape) ) ) :  #Go through all of the points in reversed order and remove the ones that are not in the reduced list
            slen=float(len(shape))                          #Used to calculate progress
            tempPosition = p.center.getPosition(frame)             #LAZY!!!
            
            if not [tempPosition[0],tempPosition[1],x] in reducedShape :
                shape.remove(x)                             #Damn, this thing is slow! (could be threaded!?)

            task.setProgress(int(((float(i)/alen)+((float(slen-x)/slen)/alen))*100.0)) #Update the progress bar
            task.setMessage("Processing point %s in brush %s (yes, this is slow)" %(x,i))  
        # except:
            # pass #Not a supported item                             

    task.setProgress(100)    

#Menu Items....
# Menu = nuke.menu('Nuke').addMenu("Roto")
# Menu.addCommand( 'Reduce Selected Brush Strokes', 'BrushReduction.reduce_selected_brush_stroke()',icon='CornerPin.png')
# Menu.addCommand( 'Reduce Selected Brush Strokes (with defaults)', 'BrushReduction.reduce_selected_brush_stroke(True)',icon='CornerPin.png')