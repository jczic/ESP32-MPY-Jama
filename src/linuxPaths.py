# -*- coding: utf-8 -*-

import os

# ------------------------------------------------------------------------

# ------------------------------------------------------------------------

def GetFilePathFromFilename(filename) :
    ospath = os.environ['PATH']
    print('Iterating $PATH:')
    for path in ospath.split(':') :
        filepath = path + "/" + filename
        print('Filepath: ' + filepath)
        if os.path.isfile(filepath) :
            return filepath
    return None

# ------------------------------------------------------------------------
