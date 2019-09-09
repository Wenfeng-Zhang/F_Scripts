import nuke

def createWriteDir(): 
    import nuke, os 
    file = nuke.filename(nuke.thisNode()) 
    dir = os.path.dirname( file ) 
    osdir = nuke.callbacks.filenameFilter( dir ) 
    try: 
        os.makedirs( osdir ) 
        return 
    except: 
        return  
        
nuke.addBeforeRender( createWriteDir )
