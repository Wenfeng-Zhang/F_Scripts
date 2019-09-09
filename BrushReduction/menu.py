import BrushReduction
#Menu Items....
toolbar = nuke.menu("Nodes")
Menu = toolbar.addMenu('F Script/Roto Reduce Strokes',)
Menu.addCommand( 'Reduce Selected Brush Strokes', 'BrushReduction.reduce_selected_brush_stroke()',icon='CornerPin.png')
Menu.addCommand( 'Reduce Selected Brush Strokes (with defaults)', 'BrushReduction.reduce_selected_brush_stroke(True)',icon='CornerPin.png')