import shuffle_short
toolbar = nuke.menu('Nodes')
m = toolbar.addMenu('F Script/Shuffle short')
m.addCommand('shuffle short +', 'shuffle_short.Shuffle_Short(1)', 'alt+up')
m.addCommand('shuffle short -', 'shuffle_short.Shuffle_Short(-1)', 'alt+down')