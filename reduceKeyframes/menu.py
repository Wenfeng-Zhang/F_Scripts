import reduceKeyframes
m=nuke.menu( 'Animation' )
m.addSeparator()
m.addCommand( 'Reduce Keyframes', "reduceKeyframes.doReduceKeyframes()", icon="CurveTool.png")