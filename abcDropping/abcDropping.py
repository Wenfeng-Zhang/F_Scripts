import nuke
import os

def abcDropping( mimeType, text):
	if text[-4:] == '.abc' and os.path.exists(text):
		readGeo = nuke.createNode('ReadGeo2', 'file {%s}' % (text))
		sceneView = readGeo['scene_view']
		allItems = sceneView.getAllItems()

		if allItems:
			sceneView.setImportedItems(allItems)
			sceneView.setSelectedItems(allItems)
		else:
			nuke.delete(readGeo)
			nuke.createNode('Camera2', 'file {%s} read_from_file True' % (text))
		return True
	return False
