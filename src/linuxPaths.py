# -*- coding: utf-8 -*-

# Thanks to Christoph Stoppe (@happenpappen)

import os

# ------------------------------------------------------------------------

def GetFilePathFromFilename(filename) :
    ospath = os.environ['PATH']
    for path in ospath.split(':') :
        filepath = path + "/" + filename
        if os.path.isfile(filepath) :
            return filepath
    return None

# ------------------------------------------------------------------------
