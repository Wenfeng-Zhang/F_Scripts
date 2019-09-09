import Open_localCachePath
toolbar = nuke.menu("Nodes")
m = toolbar.addMenu("F Script")
m.addCommand("Open_localCachePath",  "Open_localCachePath.Open_localCachePath(nuke.selectedNode())",  "alt+z",  icon="Cached.png")