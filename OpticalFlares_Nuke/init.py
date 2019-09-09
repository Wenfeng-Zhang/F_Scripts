if nuke.NUKE_VERSION_STRING.startswith('10.5'):
    import os
    op_path = os.path.dirname(__file__)

    os.putenv('OPTICAL_FLARES_LICENSE_PATH',    op_path)
    os.putenv('OPTICAL_FLARES_PATH',            op_path)
    os.putenv('OPTICAL_FLARES_PRESET_PATH',     op_path)
    nuke.pluginAddPath(op_path)

