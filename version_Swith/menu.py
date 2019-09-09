import version_Swith
toolbar = nuke.menu("Nodes")
m = toolbar.addMenu("F Script")
m.addCommand("Version Swith",  "version_Swith.versionSwith()", icon="Switch.png")