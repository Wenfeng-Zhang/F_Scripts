if nuke.NUKE_VERSION_STRING.startswith('10.5'):
    toolbar = nuke.toolbar("Nodes")
    toolbar.addMenu("VideoCopilot", icon="VideoCopilot.png")
    toolbar.addCommand( "VideoCopilot/OpticalFlares", "nuke.createNode('OpticalFlares')", icon="OpticalFlares.png")