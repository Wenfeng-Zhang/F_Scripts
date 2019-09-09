import merge_short
toolbar = nuke.menu('Nodes')
m = toolbar.addMenu('F Script')
m.addCommand('Merge shot', 'merge_short.Merge_Short()', 'alt+o')
