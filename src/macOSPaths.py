# -*- coding: utf-8 -*-

"""
Copyright © 2023 Jean-Christophe Bos (jczic.bos@gmail.com)
"""

import os
import subprocess

# ------------------------------------------------------------------------

def _getPathsInConfigContent(config) :
    paths = [ ]
    for line in config :
        if line.find('PATH') >= 0 and line.find('=') >= 0 :
            idx = line.find('"')
            if idx >= 0 :
                line = line[idx+1:]
                idx  = line.find('"')
                if idx >= 0 :
                    line = line[:idx]
                    if line.find('/') == 0 :
                        for path in line.split(':') :
                            if path and path.find('$PATH') == -1 and path.find(r'{PATH}') == -1 :
                                if path[len(path)-1] != '/' :
                                    path += '/'
                                paths.append(path)
    return paths

# ------------------------------------------------------------------------

def GetPathsInAllConfigs() :
    configFilenames = [
        # BASH SHELL :
        "/etc/bashrc",
        "/etc/profile",
        "/etc/environment",
        "~/.bashrc",
        "~/.bash_profile",
        "~/.bash_login",
        # ZSH SHELL :
        "/etc/zshrc",
        "/etc/zshenv",
        "/etc/zprofile",
        "/etc/zlogin",
        "~/.profile",
        "~/.zshrc",
        "~/.zprofile",
        "~/.zlogin"
    ]
    paths = [ ]

    try :
        proc = subprocess.Popen( ['/usr/libexec/path_helper'],
                                 stdout = subprocess.PIPE,
                                 stderr = subprocess.PIPE )
        config = [ ]
        for b in proc.stdout.readlines() :
            config.append(b.decode('UTF-8'))
        paths += _getPathsInConfigContent(config)
    except :
        pass

    for filename in configFilenames :
        try :
            filename = os.path.expanduser(filename)
            if os.path.isfile(filename) :
                with open(filename, 'r') as f :
                    paths += _getPathsInConfigContent(f.readlines())
        except :
            pass

    return paths

# ------------------------------------------------------------------------

def GetFilePathFromFilename(filename) :
    for path in GetPathsInAllConfigs() :
        filepath = path + filename
        if os.path.isfile(filepath) :
            return filepath
    return None

# ------------------------------------------------------------------------
