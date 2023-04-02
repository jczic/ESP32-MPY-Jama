# -*- coding: utf-8 -*-

"""
Copyright © 2023 Jean-Christophe Bos (jczic.bos@gmail.com)
"""

import os
import sys
from   pathlib import Path

# ============================================================================
# ===( CONFIG  )==============================================================
# ============================================================================

APPLICATION_TITLE                = 'ESP32 MPY-Jama'
APPLICATION_STR_VERSION          = '1.0.3'

APPLICATION_BUNDLE_NAME          = 'ESP32 MPY-Jama'

IS_MACOS                         = (sys.platform.upper() == 'DARWIN')
IS_LINUX                         = (sys.platform.upper() == 'LINUX')
IS_WIN32                         = (sys.platform.upper() == 'WIN32')
IS_IN_BUNDLE                     = ( getattr(sys, "frozen", False) and \
                                     hasattr(sys, '_MEIPASS') )

OS_NAME                          = 'MacOS'   if IS_MACOS else \
                                   'Linux'   if IS_LINUX else \
                                   'Windows' if IS_WIN32 else \
                                   'Unknown'

WEB_SRV_PORT                     = 11236
WEB_SRV_BIND_IP                  = '127.0.0.1'
WEB_SRV_PATH                     = 'ressources/'

HTML_SPLASH_SCREEN_FILENAME      = 'splash_scr.html'
HTML_APP_MAIN_FILENAME           = 'app_main.html'

START_GUI_AND_WS_TIMEOUT_SEC     = 3

if IS_MACOS :
    DIRECTORY_FILES              = Path('~/Library/Application Support').expanduser() / APPLICATION_BUNDLE_NAME
elif IS_LINUX :
    DIRECTORY_FILES              = Path('~/.config/').expanduser() / APPLICATION_BUNDLE_NAME
elif IS_WIN32 :
    DIRECTORY_FILES              = Path('~/AppData/Local').expanduser() / APPLICATION_BUNDLE_NAME
DIRECTORY_CONTENT_JAMA_FUNCS     = Path('Jama Funcs')
DIRECTORY_IMPORTED_JAMA_FUNCS    = DIRECTORY_FILES / 'Jama Funcs'
JAMA_FUNCS_TEMPLATE_FILENAME     = Path('Jama Funcs - Template.py')

RECURRENT_TIMER_APP_SEC          = 5

CONTENT_PATH                     = Path( ( sys.executable if IS_MACOS and IS_IN_BUNDLE
                                           else __file__ ) ) \
                                   .resolve() \
                                   .with_name("content")

PYWEBVIEW_LOCALIZATION           = { 'global.quitConfirmation': u'Do you really want to quit?',
                                     'global.ok': u'OK',
                                     'global.quit': u'Quit',
                                     'global.cancel': u'Cancel',
                                     'global.saveFile': u'Save file',
                                     'cocoa.menu.about': u'About',
                                     'cocoa.menu.services': u'Services',
                                     'cocoa.menu.view': u'View',
                                     'cocoa.menu.hide': u'Hide',
                                     'cocoa.menu.hideOthers': u'Hide Others',
                                     'cocoa.menu.showAll': u'Show All',
                                     'cocoa.menu.quit': u'Quit',
                                     'cocoa.menu.fullscreen': u'Enter Fullscreen',
                                     'windows.fileFilter.allFiles': u'All files',
                                     'windows.fileFilter.otherFiles': u'Other file types',
                                     'linux.openFile': u'Open file',
                                     'linux.openFiles': u'Open files',
                                     'linux.openFolder': u'Open folder' }

# ============================================================================
# ============================================================================
# ============================================================================
