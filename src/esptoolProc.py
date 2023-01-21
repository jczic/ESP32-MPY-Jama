# -*- coding: utf-8 -*-

"""
Copyright © 2023 Jean-Christophe Bos (jczic.bos@gmail.com)
"""

import subprocess
import conf

if conf.IS_MACOS :
    import macOSPaths
elif conf.IS_LINUX :
    import linuxPaths

_esptool = [ ]

class LaunchEsptoolException(Exception) :
    pass

# ------------------------------------------------------------------------

def GetVersion() :
    if _esptool :
        try :
            launch = _esptool + [ 'version' ]
            proc   = subprocess.Popen( launch,
                                       stdout = subprocess.PIPE,
                                       stderr = subprocess.PIPE,
                                       shell  = conf.IS_WIN32 )
            lines = proc.stdout.readlines()
            try :
                version = lines[1].decode()
                if version.find('.') > 0 :
                    return version.rstrip()
            except :
                pass
        except :
            raise LaunchEsptoolException()
    return None

# ------------------------------------------------------------------------

def CheckFirmwareImg(file) :
    if _esptool :
        try :
            launch = _esptool + [ 'image_info', file ]
            proc   = subprocess.Popen( launch,
                                       stdout = subprocess.PIPE,
                                       stderr = subprocess.PIPE,
                                       shell  = conf.IS_WIN32 )
            for line in proc.stdout.readlines() :
                line = str(line)
                if line.find('Validation Hash') >= 0 and line.find('(valid)') > 0 :
                    return True
        except :
            raise LaunchEsptoolException()
    return False

# ------------------------------------------------------------------------

def WriteFirmwareImg( imgFile,
                      chip                  = 'auto',
                      port                  = None,
                      baud                  = '230400',
                      connCallback          = None,
                      failedConnCallback    = None,
                      startsWritingCallback = None,
                      writingCallback       = None ) :
    if _esptool :
        try :
            launch = _esptool + [ '--chip', chip, '--baud', baud ]
            if port :
                launch += [ '--port', port ]
            launch += [ 'write_flash', '-z', '0x1000', imgFile ]
            proc = subprocess.Popen( launch,
                                     stdout = subprocess.PIPE,
                                     stderr = subprocess.PIPE,
                                     shell  = conf.IS_WIN32 )
            x    = ''
            port = ''
            while True :
                b = proc.stdout.read(1)
                if not b :
                    break
                x += b.decode()
                if x.find('Serial port') >= 0 and b == b'\n' :
                    port = x.rsplit(maxsplit=1)[-1]
                    if connCallback :
                        connCallback(port)
                    x = ''
                elif x.find('failed to connect') >= 0 :
                    if failedConnCallback :
                        failedConnCallback(port)
                    x = ''
                elif x.find('Flash will be erased') >= 0 :
                    if startsWritingCallback :
                        startsWritingCallback(port)
                    x = ''
                elif x.find('Hash of data verified') >= 0 :
                    return True
                else :
                    i = x.find(' %)')
                    if i > 0 :
                        percent = int( x[ x.find('(')+1 : i] )
                        if writingCallback :
                            writingCallback(port, percent)
                        x = ''
        except :
            raise LaunchEsptoolException()
    return False

# ------------------------------------------------------------------------

def EraseFlash( chip               = 'auto',
                port               = None,
                baud               = '230400',
                connCallback       = None,
                failedConnCallback = None,
                erasingCallback    = None ) :
    if _esptool :
        try :
            launch = _esptool + [ '--chip', chip, '--baud', baud ]
            if port :
                launch += [ '--port', port ]
            launch += [ 'erase_flash' ]
            proc = subprocess.Popen( launch,
                                     stdout = subprocess.PIPE,
                                     stderr = subprocess.PIPE,
                                     shell  = conf.IS_WIN32 )
            x    = ''
            port = ''
            while True :
                b = proc.stdout.read(1)
                if not b :
                    break
                x += b.decode('ASCII')
                if x.find('Serial port') >= 0 and b == b'\n' :
                    port = x.rsplit(maxsplit=1)[-1]
                    if connCallback :
                        connCallback(port)
                    x = ''
                elif x.find('failed to connect') >= 0 :
                    if failedConnCallback :
                        failedConnCallback(port)
                    x = ''
                elif x.find('Erasing flash') >= 0 :
                    if erasingCallback :
                        erasingCallback(port)
                    x = ''
                elif x.find('completed successfully') >= 0 :
                    return True
        except :
            raise LaunchEsptoolException()
    return False

# ------------------------------------------------------------------------

def _setEsptoolWin32() :
    global _esptool
    for x in ('python', 'py') :
        _esptool = [ x, '-m', 'esptool' ]
        try :
            if GetVersion() :
                return
        except :
            pass
    _esptool = [ ]

# ------------------------------------------------------------------------

if conf.IS_MACOS :
    esptoolFilename = macOSPaths.GetFilePathFromFilename('esptool.py')
    if esptoolFilename :
        _esptool = [ esptoolFilename ]
elif conf.IS_LINUX == 'LINUX' :
    esptoolFilename = linuxPaths.GetFilePathFromFilename('esptool.py')
    if esptoolFilename :
        _esptool = [ esptoolFilename ]
elif conf.IS_WIN32 == 'WIN32' :
    _setEsptoolWin32()
