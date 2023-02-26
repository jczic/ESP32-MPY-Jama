# -*- coding: utf-8 -*-

# ============================================= #
#                                               #
# Copyright © 2023 JC`zic (Jean-Christophe Bos) #
#             jczic.bos@gmail.com               #
#                                               #
# ============================================= #


from   microWebSrv     import MicroWebSrv
from   esp32Controller import *
from   random          import random
from   queue           import SimpleQueue
from   hashlib         import sha256
from   shutil          import copyfile
from   pathlib         import Path
import webview
import asyncio
import webbrowser
import esptoolProc
import json
import conf
import os
import gc

# ============================================================================
# ===( Class Application  )===================================================
# ============================================================================

class Application :

    def __init__(self) :

        self._appRunning         = False
        self._ws                 = None
        self.esp32Ctrl           = None
        self._wsMsgQueue         = SimpleQueue()
        self._contentTransfer    = None
        self._cleanAfterJamaFunc = False
        self._canCloseSoftware   = False

        self._webSrv = MicroWebSrv( port    = conf.WEB_SRV_PORT,
                                    bindIP  = conf.WEB_SRV_BIND_IP,
                                    webPath = conf.WEB_SRV_PATH )
        self._webSrv.MaxWebSocketRecvLen     = 8*1024
        self._webSrv.WebSocketThreaded       = True
        self._webSrv.AcceptWebSocketCallback = self._wsAcceptCallback

        self._splashScr = webview.create_window( '',
                                                 url        = self._localURL(conf.HTML_SPLASH_SCREEN_FILENAME),
                                                 width      = 280,
                                                 height     = 280,
                                                 resizable  = False,
                                                 frameless  = True,
                                                 on_top     = True )

        self._mainWin = webview.create_window( '%s (v%s)' % (conf.APPLICATION_TITLE, conf.APPLICATION_STR_VERSION),
                                               url        = self._localURL(conf.HTML_APP_MAIN_FILENAME),
                                               width      = 1000,
                                               height     = 680,
                                               resizable  = True,
                                               min_size   = (640, 580),
                                               hidden     = not (conf.IS_WIN32 | conf.IS_LINUX),
                                               minimized  = conf.IS_WIN32 )
        self._mainWin.events.closing += self._onMainWinClosing
        self._mainWin.events.closed  += self._onMainWinClosed
    
    # ------------------------------------------------------------------------

    @staticmethod
    def _localURL(ressource) :
        antiCache = str(random())
        return 'http://%s:%s/%s?=%s' % ( conf.WEB_SRV_BIND_IP,
                                         conf.WEB_SRV_PORT,
                                         ressource,
                                         antiCache )

    # ------------------------------------------------------------------------

    @staticmethod
    def _sizeToText(size, unity) :
        if size >= 1024*1024*1024 :
            return '%s G%s' % (round(size/1024/1024/1024*100)/100, unity[0])
        if size >= 1024*1024 :
            return '%s M%s' % (round(size/1024/1024*100)/100, unity[0])
        if size >= 1024 :
            return '%s K%s' % (round(size/1024*100)/100, unity[0])
        return '%s %s' % (size, unity)

    # ------------------------------------------------------------------------

    @staticmethod
    def _fahrenheit2Celsius(f) :
        return (f - 32) * 5/9
    
    # ------------------------------------------------------------------------

    def _onMainWinClosing(self) :
        if self._canCloseSoftware :
            return True
        self._wsSendCmd('WANT-CLOSE-SOFTWARE')
        return False

    # ------------------------------------------------------------------------

    def _onMainWinClosed(self) :
        if self._ws :
            self._ws.Close()

    # ------------------------------------------------------------------------

    def _closeSoftware(self) :
        self._canCloseSoftware = True
        self._mainWin.destroy()

    # ------------------------------------------------------------------------

    def _loadFromJSONFile(self, filename) :
        try :
            with open(filename, 'r') as f :
                o = json.load(f)
        except :
            return None
        return o

    # ------------------------------------------------------------------------

    def _saveToJSONFile(self, o, filename, indent=False) :
        try :
            with open(filename, 'w') as f :
                json.dump( o,
                           f,
                           indent = ('\t' if indent else None) )
        except :
            return False
        return True

    # ------------------------------------------------------------------------

    def _wsSendCmd(self, cmdName, oArg=None) :
        if self._ws :
            o = {
                "CMD" : cmdName,
                "ARG" : oArg
            }
            try :
                return self._ws.SendText(json.dumps(o))
            except :
                pass
        return False

    # ------------------------------------------------------------------------

    def _wsProcessMessage(self, o) :
        try :
            cmd = o['CMD'].upper()
            arg = o['ARG']
            if   cmd == 'GET-SERIAL-PORTS' :
                self._sendSerialPorts()
            elif cmd == 'CONNECT-SERIAL' :
                self._connectSerial(arg)
            elif cmd == 'DISCONNECT-SERIAL' :
                self._disconnectSerial()
            elif cmd == 'GET-SYS-INFO' :
                self._sendSysInfo(arg)
            elif cmd == 'GET-NETWORKS-INFO' :
                self._sendNetworksInfo(arg)
            elif cmd == 'CLOSE-INTERFACE' :
                self._closeInterface(arg)
            elif cmd == 'GET-WIFI-NETWORKS' :
                self._sendWiFiNetworks()
            elif cmd == 'WIFI-CONNECT' :
                self._wifiConnect(arg['ssid'], arg['key'])
            elif cmd == 'WIFI-SAVE' :
                self._wifiSave(arg['ssid'], arg['key'])
            elif cmd == 'WIFI-OPEN-AP' :
                self._wifiOpenAP(arg['ssid'], arg['auth'], arg['key'], arg['maxcli'])
            elif cmd == 'EXEC-CODE' :
                self._execCode(arg['code'], arg['codeFilename'])
            elif cmd == 'EXEC-CODE-STOP' :
                self._execCodeStop()
            elif cmd == 'GET-FLASH-ROOT-PATH' :
                self._sendFlashRootPath()
            elif cmd == 'GET-PINS-LIST' :
                self._sendPinsList(arg)
            elif cmd == 'GET-LIST-DIR' :
                self._sendListDir(arg)
            elif cmd == 'CREATE-DIR' :
                self._createDir(arg)
            elif cmd == 'RENAME-FILE-OR-DIR' :
                self._renameFileOrDir(arg['srcPath'], arg['dstPath'])
            elif cmd == 'DELETE-FILE-OR-DIR' :
                self._deleteFileOrRecurDir(arg)
            elif cmd == 'DOWNLOAD-FILE' :
                self._downloadFile(arg)
            elif cmd == 'UPLOAD-FILE' :
                self._uploadFile(arg)
            elif cmd == 'GET-FILE-CONTENT' :
                self._sendFileContent(arg)
            elif cmd == 'START-CONTENT-TRANSFER' :
                self._startContentTransfer(arg['name'], arg['size'])
            elif cmd == 'FILE-CONTENT-DATA' :
                self._recvFileContentData(arg)
            elif cmd == 'PROGRAM-CONTENT-DATA' :
                self._recvProgramContentData(arg)
            elif cmd == 'GET-ESPTOOL-VER' :
                self._sendEsptoolVersion()
            elif cmd == 'WRITE-FIRMWARE' :
                self._esp32WriteFirmwareImg(arg)
            elif cmd == 'IMPORT-JAMA-FUNC' :
                self._importJamaFunc()
            elif cmd == 'EXPORT-JAMA-FUNC' :
                self._exportJamaFunc(arg)
            elif cmd == 'SAVE-JAMA-FUNCS-TEMPLATE' :
                self._saveJamaFuncsTemplate()
            elif cmd == 'DELETE-JAMA-FUNC' :
                self._deleteJamaFunc(arg)
            elif cmd == 'GET-ALL-JAMA-FUNCS-CONFIG' :
                self._sendAllJamaFuncsConfig()
            elif cmd == 'EXEC-JAMA-FUNC' :
                self._execJamaFunc(arg['config'], arg['values'])
            elif cmd == 'ERASE-FLASH' :
                self._esp32EraseFlash(arg)
            elif cmd == 'RESET' :
                self._reset()
            elif cmd == 'GET-MODULES' :
                self._sendModules()
            elif cmd == 'EXEC-PY-FILE' :
                self._executePYFile(arg)
            elif cmd == 'IMPORT-MODULE' :
                self._importModule(arg)
            elif cmd == 'INSTALL-PACKAGE' :
                self._installPackage(arg)
            elif cmd == 'SET-MCU-FREQ' :
                self._setMCUFreq(arg)
            elif cmd == 'SDCARD-INIT' :
                self._initSDCard()
            elif cmd == 'SDCARD-FORMAT' :
                self._formatSDCard()
            elif cmd == 'GET-SDCARD-CONF' :
                self._sendSDCardConf(arg)
            elif cmd == 'SDCARD-MOUNT' :
                self._mountSDCard(arg)
            elif cmd == 'SDCARD-UMOUNT' :
                self._umountSDCard()
            elif cmd == "CLOSE-SOFTWARE" :
                self._closeSoftware()
            elif cmd == "OPEN-URL" :
                webbrowser.open_new_tab(str(arg))
        except :
            pass

    # ------------------------------------------------------------------------

    def _wsAcceptCallback(self, webSocket, httpClient) :
        if self._ws :
            webSocket.Close()
            return
        self._ws                   = webSocket
        webSocket.RecvTextCallback = self._wsRecvTextCallback
        webSocket.ClosedCallback   = self._wsClosedCallback
        self._wsSendCmd('VERSION', 'v' + conf.APPLICATION_STR_VERSION)
        if self._splashScr :
            self._splashScr.destroy()
            self._splashScr = None
            if conf.IS_WIN32 :
                self._mainWin.restore()
            else :
                self._mainWin.show()

    # ------------------------------------------------------------------------

    def _wsRecvTextCallback(self, webSocket, msg) :
        try :
            o = json.loads(msg)
            self._wsMsgQueue.put(o)
        except :
            webSocket.Close()
            self._ws = None

    # ------------------------------------------------------------------------

    def _wsClosedCallback(self, webSocket) :
        self._ws = None

    # ------------------------------------------------------------------------

    def _sendSerialPorts(self) :
        list = [ dict( Device = '', Name = 'Automatic port detection', USB = None) ]
        for port in ESP32Controller.GetSerialPorts() :
            desc = ( (' (%s)' % port['Desc']) if port['Desc'] != 'n/a' else '' )
            list.append( dict(
                Device = port['Device'],
                Name   = '%s port %s%s' % (('USB' if port['USB'] else 'Serial'), port['Name'], desc),
                USB    = port['USB'] ) )
        self._wsSendCmd('SERIAL-PORTS', list)

    # ------------------------------------------------------------------------

    def _connectSerial(self, devicePort) :
        if not self.esp32Ctrl :
            Err = None
            if devicePort :
                self._wsSendCmd('SHOW-WAIT', 'Try to connect to the device...')
                try :
                    self.esp32Ctrl = ESP32Controller( devicePort        = devicePort,
                                                      connectTimeoutSec = 7,
                                                      onSerialConnError = self._onSerialConnError,
                                                      onTerminalRecv    = self._onTerminalRecv,
                                                      onEndOfProgram    = self._onEndOfProgram,
                                                      onProgramError    = self._onProgramError,
                                                      onProgramStopped  = self._onProgramStopped,
                                                      onDeviceReset     = self._onDeviceReset )
                except Exception as ex :
                    Err = str(ex)
            else :
                self._wsSendCmd('SHOW-WAIT', 'Search for a device to connect to...')
                self.esp32Ctrl = ESP32Controller.GetFirstAvailableESP32Ctrl( onSerialConnError = self._onSerialConnError,
                                                                             onTerminalRecv    = self._onTerminalRecv,
                                                                             onEndOfProgram    = self._onEndOfProgram,
                                                                             onProgramError    = self._onProgramError,
                                                                             onProgramStopped  = self._onProgramStopped,
                                                                             onDeviceReset     = self._onDeviceReset )
            self._wsSendCmd('HIDE-WAIT')
            if self.esp32Ctrl :
                self._wsSendCmd('SERIAL-CONNECTED', True)
                self._wsSendCmd('DEVICE-INFO', dict( deviceMCU    = self.esp32Ctrl.GetDeviceMCU(),
                                                     deviceModule = self.esp32Ctrl.GetDeviceModule() ))
                self._wsSendCmd('SHOW-ALERT', "Port %s connected to %s." % (self.esp32Ctrl.GetDevicePort(), self.esp32Ctrl.GetDeviceMCU()))
                self._sendFlashRootPath()
                self._sendSDCardConf(silence=True)
                self._sendPinsList()
                self._sendAutoInfo()
            else :
                self._wsSendCmd('SHOW-ERROR', Err if Err else 'No compatible device was found.')

    # ------------------------------------------------------------------------

    def _disconnectSerial(self) :
        if self.esp32Ctrl :
            self.esp32Ctrl.Close()
            self._wsSendCmd('SERIAL-CONNECTED', False)
            self._wsSendCmd('SHOW-ALERT', 'Port %s disconnected from %s.' % (self.esp32Ctrl.GetDevicePort(), self.esp32Ctrl.GetDeviceMCU()))
            self._wsSendCmd('EXEC-CODE-END', False)
            self._cleanAfterJamaFunc = False
            self.esp32Ctrl = None

    # ------------------------------------------------------------------------

    def _onSerialConnError(self, esp32Ctrl) :
        self._wsSendCmd('SERIAL-CONNECTED', False)
        self._wsSendCmd('SHOW-ERROR', 'You have been disconnected from the device.')
        self._wsSendCmd('EXEC-CODE-END', False)
        self._cleanAfterJamaFunc = False
        self.esp32Ctrl = None
        
    # ------------------------------------------------------------------------

    def _onTerminalRecv(self, esp32Ctrl, text) :
        self._wsSendCmd('EXEC-CODE-RECV', text)
        
    # ------------------------------------------------------------------------

    def _onEndOfProgram(self, esp32Ctrl) :
        self._wsSendCmd('EXEC-CODE-END', True)
        
    # ------------------------------------------------------------------------

    def _onProgramError(self, esp32Ctrl, error) :
        self._wsSendCmd('EXEC-CODE-ERROR', error)
        self._wsSendCmd('EXEC-CODE-END', False)
        
    # ------------------------------------------------------------------------

    def _onProgramStopped(self, esp32Ctrl) :
        self._wsSendCmd('EXEC-CODE-STOPPED')
        self._wsSendCmd('EXEC-CODE-END', False)
        
    # ------------------------------------------------------------------------

    def _onDeviceReset(self, esp32Ctrl) :
        self._wsSendCmd('DEVICE-RESET')
        self._wsSendCmd('EXEC-CODE-END', False)
        self._wsSendCmd('SHOW-ALERT', 'The device has been reset!')
        self._cleanAfterJamaFunc = False
        
    # ------------------------------------------------------------------------

    def _ableToUseDevice(self, silence=False) :
        if not self.esp32Ctrl or not self.esp32Ctrl.IsConnected() :
            if not silence :
                self._wsSendCmd('SHOW-INFO', 'The device must be connected first.')
        elif self.esp32Ctrl.IsProcessing() :
            if not silence :
                self._wsSendCmd('SHOW-INFO', 'The device is already in use.')
        else :
            return True
        return False

    # ------------------------------------------------------------------------

    def _recvFile(self, remoteFilename, localFilename) :
        if self._ableToUseDevice() :
            try :
                self.esp32Ctrl.RecvFile(remoteFilename, localFilename, self._recvFileProgress)
                self._wsSendCmd('HIDE-PROGRESS')
            except ESP32ControllerException as esp32CtrlEx :
                self._wsSendCmd('HIDE-PROGRESS')
                if self.esp32Ctrl :
                    self._wsSendCmd('SHOW-ERROR', str(esp32CtrlEx))
            except :
                self._wsSendCmd('HIDE-PROGRESS')
                self._wsSendCmd('SHOW-ERROR', 'An error has occurred.')

    def _recvFileProgress(self, progress, fileSize) :
        self._wsSendCmd( 'SHOW-PROGRESS',
                         dict( text    = 'Receiving file from device... (%s)' % self._sizeToText(progress, 'octets'),
                               percent = progress * 100 // fileSize ) )

    # ------------------------------------------------------------------------

    def _sendFile(self, localFilename, remoteFilename) :
        if self._ableToUseDevice() :
            try :
                self.esp32Ctrl.SendFile(localFilename, remoteFilename, self._sendFileProgress)
                self._wsSendCmd('HIDE-PROGRESS')
            except ESP32ControllerException as esp32CtrlEx :
                self._wsSendCmd('HIDE-PROGRESS')
                if self.esp32Ctrl :
                    self._wsSendCmd('SHOW-ERROR', str(esp32CtrlEx))
            except :
                self._wsSendCmd('HIDE-PROGRESS')
                self._wsSendCmd('SHOW-ERROR', 'An error has occurred.')

    def _sendFileProgress(self, progress, fileSize) :
        self._wsSendCmd( 'SHOW-PROGRESS',
                         dict( text    = 'Sending file to device... (%s)' % self._sizeToText(progress, 'octets'),
                               percent = progress * 100 // fileSize ) )

    # ------------------------------------------------------------------------

    def _downloadFile(self, remoteFilename) :
        if self._ableToUseDevice() :
            filename = remoteFilename.split('/')[-1]
            if filename :
                r = self._mainWin.create_file_dialog( webview.SAVE_DIALOG,
                                                      directory     = '',
                                                      save_filename = filename )
                if r :
                    self._recvFile(remoteFilename, r)

    # ------------------------------------------------------------------------

    def _uploadFile(self, remoteFilePath) :
        if self._ableToUseDevice() :
            file_types = ('All files (*.*)', )
            r = self._mainWin.create_file_dialog( webview.OPEN_DIALOG,
                                                  allow_multiple = False,
                                                  file_types     = file_types )
            if r and len(r) == 1 :
                localFilename  = r[0]
                remoteFilename = remoteFilePath + Path(localFilename).name
                self._sendFile(localFilename, remoteFilename)

    # ------------------------------------------------------------------------

    def _sendFileContent(self, remoteFilename) :
        if self._ableToUseDevice() :
            try :
                self.esp32Ctrl.GetFileContent(remoteFilename, self._getFileContentProgress)
                self._wsSendCmd('HIDE-PROGRESS')
                self._wsSendCmd('END-OF-GET-FILE-CONTENT')
            except :
                self._wsSendCmd('HIDE-PROGRESS')
                self._wsSendCmd('SHOW-ERROR', 'An error has occurred.')

    def _getFileContentProgress(self, progress, fileSize, newData) :
        if newData :
            self._wsSendCmd('FILE-CONTENT-DATA', list(newData))
        self._wsSendCmd( 'SHOW-PROGRESS',
                         dict( text    = 'Loading file from device...',
                               percent = progress * 100 // fileSize ) )

    # ------------------------------------------------------------------------

    def _startContentTransfer(self, name, size) :
        if self._ableToUseDevice() :
            self._contentTransfer = dict( name = name,
                                          size = size,
                                          data = b'' )

    # ------------------------------------------------------------------------

    def _recvFileContentData(self, data) :
        if self._contentTransfer :
            self._contentTransfer['data'] += bytes(data)
            if len(self._contentTransfer['data']) == self._contentTransfer['size'] :
                try :
                    self.esp32Ctrl.PutFileContent( self._contentTransfer['name'],
                                                   self._contentTransfer['data'],
                                                   self._putFileContentProgress )
                    self._wsSendCmd('HIDE-PROGRESS')
                    self._wsSendCmd('END-OF-FILE-CONTENT-DATA')
                except :
                    self._wsSendCmd('HIDE-PROGRESS')
                    self._wsSendCmd('SHOW-ERROR', 'An error has occurred.')

    def _putFileContentProgress(self, progress, fileSize) :
        self._wsSendCmd( 'SHOW-PROGRESS',
                         dict( text    = 'Saving file to device...',
                               percent = progress * 100 // fileSize ) )

    # ------------------------------------------------------------------------

    def _recvProgramContentData(self, data) :
        if self._contentTransfer :
            self._contentTransfer['data'] += bytes(data)
            if len(self._contentTransfer['data']) == self._contentTransfer['size'] :
                try :
                    self.esp32Ctrl.ExecProgram( code         = self._contentTransfer['data'].decode(),
                                                codeFilename = self._contentTransfer['name'],
                                                cbProgress   = self._execProgramProgress )
                except :
                    self._wsSendCmd('HIDE-PROGRESS')
                    self._wsSendCmd('EXEC-CODE-END', False)
                    self._wsSendCmd('SHOW-ERROR', 'An error has occurred.')

    def _execProgramProgress(self, progress, size) :
        if progress < size :
            self._wsSendCmd( 'SHOW-PROGRESS',
                             dict( text    = 'Loading program into device...',
                                   percent = progress * 100 // size ) )
        else :
            self._wsSendCmd('HIDE-PROGRESS')
            self._wsSendCmd('EXEC-CODE-BEGIN')

    # ------------------------------------------------------------------------

    def _sendFlashRootPath(self) :
        if self._ableToUseDevice() :
            try :
                self._wsSendCmd('FLASH-ROOT-PATH', self.esp32Ctrl.GetFlashRootPath())
            except :
                self._wsSendCmd('SHOW-ERROR', 'An error has occurred.')

    # ------------------------------------------------------------------------

    def _sendListDir(self, path) :
        if self._ableToUseDevice(silence=True) :
            try :
                try :
                    entries = self.esp32Ctrl.GetListDir(path)
                except :
                    path    = self.esp32Ctrl.GetFlashRootPath()
                    entries = self.esp32Ctrl.GetListDir(path)
                self._wsSendCmd('LIST-DIR', dict( path = path, entries = entries ))
            except :
                self._wsSendCmd('SHOW-ERROR', 'An error has occurred.')

    # ------------------------------------------------------------------------

    def _createDir(self, path) :
        if self._ableToUseDevice() :
            try :
                self.esp32Ctrl.CreateDir(path)
            except :
                self._wsSendCmd('SHOW-ERROR', 'Unable to create this directory.')

    # ------------------------------------------------------------------------

    def _renameFileOrDir(self, srcPath, dstPath) :
        if self._ableToUseDevice() :
            try :
                self.esp32Ctrl.RenameFileOrDir(srcPath, dstPath)
            except :
                self._wsSendCmd('SHOW-ERROR', 'Unable to rename this element.')

    # ------------------------------------------------------------------------

    def _deleteFileOrRecurDir(self, path) :
        if self._ableToUseDevice() :
            try :
                self.esp32Ctrl.DeleteFileOrRecurDir(path)
            except :
                self._wsSendCmd('SHOW-ERROR', 'Unable to remove this element.')

    # ------------------------------------------------------------------------
    
    def _sendPinsList(self, silence=False) :
        if self._ableToUseDevice(silence) :
            try :
                self._wsSendCmd('PINS-LIST', self.esp32Ctrl.GetPinsState())
            except :
                self._wsSendCmd('SHOW-ERROR', 'An error has occurred.')

    # ------------------------------------------------------------------------

    def _sendSysInfo(self, silence) :
        if self._ableToUseDevice(silence) :
            if not silence :
                self._wsSendCmd('SHOW-WAIT', 'Collecting informations...')
            try :
                o = dict( freq      = self.esp32Ctrl.GetMHzFreq(),
                          flashSize = self.esp32Ctrl.GetFlashSize(),
                          os        = self.esp32Ctrl.GetPlatformInfo(),
                          pins      = self.esp32Ctrl.GetPinsState() )
                if not silence :
                    self._wsSendCmd('HIDE-WAIT')
                self._wsSendCmd('SYS-INFO', o)
            except :
                if not silence :
                    self._wsSendCmd('HIDE-WAIT')
                    self._wsSendCmd('SHOW-ERROR', 'An error has occurred.')

    # ------------------------------------------------------------------------

    def _sendNetworksInfo(self, silence) :
        if self._ableToUseDevice(silence) :
            if not silence :
                self._wsSendCmd('SHOW-WAIT', 'Collecting informations...')
            try :
                wifiSTACnf = self.esp32Ctrl.GetWiFiConfig(ap=False)
                wifiAPCnf  = self.esp32Ctrl.GetWiFiConfig(ap=True)
                internetOk = self.esp32Ctrl.GetInternetOk()
                try :
                    bleActive = self.esp32Ctrl.GetBLEActive()
                    bleMAC    = self.esp32Ctrl.GetBLEMacAddr()
                except :
                    bleActive = False
                    bleMAC    = 'Not available'
                o = dict( wifiSTA = dict(
                              active  = self.esp32Ctrl.GetWiFiActive(ap=False),
                              mac     = self.esp32Ctrl.GetWiFiMacAddr(ap=False),
                              ssid    = wifiSTACnf['ssid'],
                              ip      = wifiSTACnf['ip'],
                              mask    = wifiSTACnf['mask'],
                              gateway = wifiSTACnf['gateway'],
                              dns     = wifiSTACnf['dns']
                          ),
                          wifiAP = dict(
                              active  = self.esp32Ctrl.GetWiFiActive(ap=True),
                              mac     = self.esp32Ctrl.GetWiFiMacAddr(ap=True),
                              ssid    = wifiAPCnf['ssid'],
                              ip      = wifiAPCnf['ip'],
                              mask    = wifiAPCnf['mask'],
                              gateway = wifiAPCnf['gateway'],
                              dns     = wifiAPCnf['dns']
                          ),
                          ble = dict(
                              active  = bleActive,
                              mac     = bleMAC
                          ),
                          internetOK = internetOk
                )
                if not silence :
                    self._wsSendCmd('HIDE-WAIT')
                self._wsSendCmd('NETWORKS-INFO', o)
            except :
                if not silence :
                    self._wsSendCmd('HIDE-WAIT')
                    self._wsSendCmd('SHOW-ERROR', 'An error has occurred.')

    # ------------------------------------------------------------------------

    def _closeInterface(self, interface) :
        if self._ableToUseDevice() :
            try :
                interface = interface.upper()
                if   interface == 'STA' :
                    self.esp32Ctrl.CloseWiFi(ap=False)
                elif interface == 'AP' :
                    self.esp32Ctrl.CloseWiFi(ap=True)
                elif interface == 'BLE' :
                    self.esp32Ctrl.CloseBLE()
                else :
                    raise Exception()
                self._wsSendCmd('INTERFACE-CLOSED', interface)
            except :
                self._wsSendCmd('SHOW-ERROR', 'Unable to close this interface.')

    # ------------------------------------------------------------------------

    def _sendWiFiNetworks(self) :
        if self._ableToUseDevice() :
            self._wsSendCmd('SHOW-WAIT', 'Scanning Wi-Fi networks from the device...')
            try :
                networks = self.esp32Ctrl.ScanWiFiNetworks()
                self._wsSendCmd('HIDE-WAIT')
                if networks :
                    self._wsSendCmd('WIFI-NETWORKS', networks)
                else :
                    self._wsSendCmd('SHOW-INFO', 'No Wi-Fi networks found.')
            except :
                self._wsSendCmd('HIDE-WAIT')
                self._wsSendCmd('SHOW-ERROR', 'An error has occurred.')

    # ------------------------------------------------------------------------

    def _wifiConnect(self, ssid, key) :
        if self._ableToUseDevice() :
            self._wsSendCmd('SHOW-WAIT', 'Connecting to access point %s from the device...' % ssid)
            try :
                ok = self.esp32Ctrl.WiFiConnect(ssid, key)
                self._wsSendCmd('HIDE-WAIT')
                if ok :
                    self._wsSendCmd('SHOW-ALERT', 'The device is connected to the %s access point.' % ssid)
                    self._wsSendCmd('WIFI-CONNECTED', { "ssid": ssid, "key": key })
                else :
                    self._wsSendCmd('SHOW-ERROR', 'Unable to connect the device to access point %s.' % ssid)
            except :
                self._wsSendCmd('HIDE-WAIT')
                self._wsSendCmd('SHOW-ERROR', 'An error has occurred.')

    # ------------------------------------------------------------------------

    def _wifiSave(self, ssid, key) :
        if self._ableToUseDevice() :
            try :
                self.esp32Ctrl.WiFiSave(ssid, key)
            except :
                self._wsSendCmd('SHOW-ERROR', 'Unable to save Wi-Fi configuration.')

    # ------------------------------------------------------------------------

    def _wifiOpenAP(self, ssid, auth, key, maxcli) :
        if self._ableToUseDevice() :
            self._wsSendCmd('SHOW-WAIT', 'Opening the access point %s...' % ssid)
            try :
                self.esp32Ctrl.WifiOpenAP( ssid   = ssid,
                                           auth   = auth,
                                           key    = key,
                                           maxcli = maxcli )
                self._wsSendCmd('HIDE-WAIT')
                self._wsSendCmd('SHOW-ALERT', 'The Wi-Fi access point has been opened.')
                self._wsSendCmd('WIFI-AP-OPENED', ssid)
            except :
                self._wsSendCmd('HIDE-WAIT')
                self._wsSendCmd('SHOW-ERROR', 'Unable to open the Wi-Fi access point.')

    # ------------------------------------------------------------------------

    def _execCode(self, code, codeFilename=None) :
        if self._ableToUseDevice() :
            try :
                self.esp32Ctrl.ExecProgram( code         = code,
                                            codeFilename = codeFilename,
                                            cbProgress   = self._execCodeProgress )
            except :
                self._wsSendCmd('EXEC-CODE-END', False)
                self._wsSendCmd('SHOW-ERROR', 'An error has occurred.')
        else :
            self._wsSendCmd('EXEC-CODE-END', False)

    def _execCodeProgress(self, progress, size) :
        if progress == size :
            self._wsSendCmd('EXEC-CODE-BEGIN')

    # ------------------------------------------------------------------------

    def _execCodeStop(self) :
        if self.esp32Ctrl and self.esp32Ctrl.IsConnected() and self.esp32Ctrl.IsProcessing() :
            try :
                self._wsSendCmd('SHOW-WAIT', 'Attempt to interrupt the program...')
                if self.esp32Ctrl.InterruptProgram() :
                    self._wsSendCmd('HIDE-WAIT')
                else :
                    self.esp32Ctrl.Close(kill=True)
                    self.esp32Ctrl = None
                    self._wsSendCmd('EXEC-CODE-STOPPED')
                    self._wsSendCmd('EXEC-CODE-END', False)
                    self._wsSendCmd('SERIAL-CONNECTED', False)
                    self._wsSendCmd('HIDE-WAIT')
                    self._wsSendCmd('SHOW-ERROR', 'The device did not respond correctly...\nThe connection had to be closed.\n\n' \
                                                + 'Your ESP32 may need an electrical reboot.')
                    self._cleanAfterJamaFunc = False
            except :
                self._wsSendCmd('SHOW-ERROR', 'An error has occurred.')
    
    # ------------------------------------------------------------------------

    def _sendEsptoolVersion(self) :
        try :
            ver = esptoolProc.GetVersion()
        except :
            ver = None
        self._wsSendCmd('ESPTOOL-VER', ver)

    # ------------------------------------------------------------------------

    def _onEspToolConn(self, port) :
        self._wsSendCmd('SHOW-WAIT', 'Try to connect to the device on port\n%s...' % port)
    
    # ------------------------------------------------------------------------

    def _onEspToolStartsWriting(self, port) :
        self._wsSendCmd( 'HIDE-WAIT' )
        self._wsSendCmd( 'SHOW-PROGRESS',
                         dict( text    = 'Starts writing to the device\'s flash memory on port %s...' % port,
                               percent = 0 ) )

    # ------------------------------------------------------------------------

    def _onEspToolWriting(self, port, percent) :
        self._wsSendCmd( 'SHOW-PROGRESS',
                         dict( text    = 'Writing the firmware image to the device\'s flash memory on port %s...' % port,
                               percent = percent ) )

    # ------------------------------------------------------------------------

    def _esp32WriteFirmwareImg(self, port) :
        file_types = ('Firmware image files (*.bin)', )
        imgFile    = self._mainWin.create_file_dialog( webview.OPEN_DIALOG,
                                                       allow_multiple = False,
                                                       file_types     = file_types )
        if imgFile and len(imgFile) == 1 :
            imgFile = imgFile[0]
            try :
                if esptoolProc.CheckFirmwareImg(imgFile) :
                    ok = esptoolProc.WriteFirmwareImg( imgFile,
                                                       port                  = port,
                                                       connCallback          = self._onEspToolConn,
                                                       startsWritingCallback = self._onEspToolStartsWriting,
                                                       writingCallback       = self._onEspToolWriting )
                    self._wsSendCmd('HIDE-WAIT')
                    self._wsSendCmd('HIDE-PROGRESS')
                    if ok :
                        self._wsSendCmd('SHOW-INFO', 'The firmware image has been successfully written to the device\'s flash memory.\nYou can restart it!')
                    else :
                        self._wsSendCmd('SHOW-ERROR', 'Unable to write the firmware image to the device\'s flash memory.')
                else :
                    self._wsSendCmd('SHOW-ERROR', 'This file is not a valid firmware image.')
            except :
                self._wsSendCmd('SHOW-ERROR', 'Unable to launch esptool.')

    # ------------------------------------------------------------------------
    
    def _onEspToolErasing(self, port) :
        self._wsSendCmd('SHOW-WAIT', 'Erasing device\'s flash memory on port\n%s...' % port)

    # ------------------------------------------------------------------------

    def _esp32EraseFlash(self, port) :
        try :
            ok = esptoolProc.EraseFlash( port            = port,
                                         connCallback    = self._onEspToolConn,
                                         erasingCallback = self._onEspToolErasing )
            self._wsSendCmd('HIDE-WAIT')
            if ok :
                self._wsSendCmd('SHOW-INFO', 'The device\'s flash memory has been successfully erased.')
            else :
                self._wsSendCmd('SHOW-ERROR', 'Unable to erase the device\'s flash memory.')
        except :
            self._wsSendCmd('SHOW-ERROR', 'Unable to launch esptool.')

    # ------------------------------------------------------------------------

    def _loadJamaFuncConfig(self, filename) :
        confPy = None
        err    = None
        try :
            with open(filename, 'r') as f :
                while True :
                    line = f.readline()
                    if not line :
                        if confPy is None :
                            err = 'Couldn\'t find comment "%s" to start reading the config.' % 'START_CONFIG_PARAMETERS'
                        else :
                            err = 'Couldn\'t find the comment "%s" to end reading the config.' % 'END_CONFIG_PARAMETERS'
                        break
                    if confPy is not None :
                        if line.find('END_CONFIG_PARAMETERS') >= 0 :
                            try :
                                config = eval(confPy)
                                config['filename'] = filename
                                return config
                            except Exception as configEx :
                                try :
                                    err = 'Invalid configuration, %s\n%s' % (configEx.args[0], configEx.args[1][3])
                                except :
                                    err = 'Invalid configuration: %s.' % str(configEx)
                            break
                        else :
                            confPy += line
                    elif line.find('START_CONFIG_PARAMETERS') >= 0 :
                        confPy = ''
        except :
            err = 'Unable to read the file %s.' % filename
        raise Exception(err)

    # ------------------------------------------------------------------------

    def _jamaFuncConfigError(self, config) :
        def fieldErr(dictio, field, fieldType, canBeEmpty=False) :
            try :
                x = dictio.get(field) if field else dictio
                if not x :
                    return not canBeEmpty
                return not isinstance(x, fieldType)
            except :
                return True
        if fieldErr(config, None, dict) :
            return 'Invalid configuration structure.'
        if fieldErr(config, 'info', dict) :
            return 'Invalid or empty info in configuration structure.'
        info = config['info']
        if fieldErr(info, 'name', str) :
            return 'Invalid or empty name in info configuration structure.'
        if fieldErr(info, 'version', list) or len(info['version']) != 3 or not isinstance(info['version'][0], int) or \
           not isinstance(info['version'][1], int) or not isinstance(info['version'][2], int) :
            return 'Invalid or empty version in info configuration structure.'
        if fieldErr(info, 'description', str) :
            return 'Invalid or empty description in info configuration structure.'
        if fieldErr(info, 'author', str) :
            return 'Invalid or empty author in info configuration structure.'
        if fieldErr(info, 'mail', str, True) :
            return 'Invalid mail in info configuration structure.'
        if fieldErr(info, 'www', str, True) :
            return 'Invalid web link in info configuration structure.'
        timeout = config.get('timeout')
        if fieldErr(config, 'timeout', int, True) or (timeout and timeout < 0) :
            return 'Invalid timeout in configuration structure.'
        if fieldErr(config, 'args', dict, True) :
            return 'Invalid args in configuration structure.'
        args = config.get('args')
        if args :
            for arg in args :
                if fieldErr(args, arg, dict) :
                    return 'Invalid or empty argument "%s" in args configuration structure.' % arg
                if fieldErr(args[arg], 'label', str) :
                    return 'Invalid or empty argument label of "%s" in args configuration structure.' % arg
                if fieldErr(args[arg], 'type', type) :
                    return 'Invalid or empty argument type of "%s" in args configuration structure.' % arg
                t = args[arg]['type']
                if t not in (str, int, float, bool, list, dict) :
                    return '"%s" is not a valid type for "%s" in args configuration structure.' % (t.__name__, arg)
                if t == str and fieldErr(args[arg], 'value', str, True) :
                    return 'The value of arg "%s" is not of type "str".' % arg
                elif t == int and fieldErr(args[arg], 'value', int, True) :
                    return 'The value of arg "%s" is not of type "int".' % arg
                elif t == float and fieldErr(args[arg], 'value', (int, float), True) :
                    return 'The value of arg "%s" is not of type "float" or "int".' % arg
                elif t == bool and fieldErr(args[arg], 'value', bool, True) :
                    return 'The value of arg "%s" is not of type "bool".' % arg
                elif t == list and fieldErr(args[arg], 'optional', bool, True) :
                    return 'The optional value of arg "%s" is not of type "bool".' % arg
                elif t == dict :
                    if fieldErr(args[arg], 'items', dict) :
                        return 'Invalid or empty argument dict items of "%s" in args configuration structure.' % arg
                    items = args[arg]['items']
                    for item in items :
                        if fieldErr(items, item, str) :
                            return 'Invalid or empty argument item "%s" of "%s" in args configuration structure.' % (item, arg)
                    if fieldErr(args[arg], 'value', str, True) :
                        return 'The value of arg "%s" is not of type "str".' % arg
                args[arg]['type'] = t.__name__
        return None

    # ------------------------------------------------------------------------

    def _importJamaFunc(self) :
        file_types = ('Jama Funcs MicroPython Files (*.py)', )
        filename   = self._mainWin.create_file_dialog( webview.OPEN_DIALOG,
                                                       allow_multiple = False,
                                                       file_types     = file_types )
        if filename and len(filename) == 1 :
            filename = filename[0]
            try :
                config = self._loadJamaFuncConfig(filename)
                error  = self._jamaFuncConfigError(config)
                if error :
                    raise Exception(error)
                try :
                    with open(filename, 'rb') as f :
                        hash = sha256(f.read()).digest().hex()
                    destFilename = conf.DIRECTORY_IMPORTED_JAMA_FUNCS / (hash + '.py')
                    info = config['info']
                    ver  = '%s.%s.%s' % tuple(info['version'])
                    try :
                        os.stat(destFilename)
                        self._wsSendCmd('SHOW-INFO', '%s v%s already exists.' % (info['name'], ver))
                    except :
                        copyfile(filename, destFilename)
                        self._wsSendCmd( 'SHOW-INFO',
                                         'The Jama Func %s v%s by %s has been successfully imported.'
                                         % (info['name'], ver, info['author']) )
                        self._wsSendCmd('JAMA-FUNC-IMPORTED', config)
                except :
                    raise Exception('An error occurred while processing the file.')
            except Exception as ex :
                self._wsSendCmd('SHOW-ERROR', str(ex))

    # ------------------------------------------------------------------------

    def _exportJamaFunc(self, config) :
        try :
            filename = config['filename']
            r = self._mainWin.create_file_dialog( webview.SAVE_DIALOG,
                                                  directory     = '',
                                                  save_filename = 'Jama Func.py' )
            if r :
                copyfile(filename, r)
                info = config['info']
                ver  = '%s.%s.%s' % tuple(info['version'])
                self._wsSendCmd( 'SHOW-INFO',
                                 'The Jama Func %s v%s by %s has been successfully exported.'
                                 % (info['name'], ver, info['author']) )
        except :
            self._wsSendCmd('SHOW-ERROR', 'An error occurred while exporting this element.')

    # ------------------------------------------------------------------------

    def _saveJamaFuncsTemplate(self) :
        try :
            r = self._mainWin.create_file_dialog( webview.SAVE_DIALOG,
                                                  directory     = '',
                                                  save_filename = 'Jama Funcs - Template.py' )
            if r :
                copyfile(conf.JAMA_FUNCS_TEMPLATE_FILENAME, r)
                self._wsSendCmd('SHOW-INFO', 'The template has been successfully saved.')
        except :
            self._wsSendCmd('SHOW-ERROR', 'An error occurred while saving the template.')

    # ------------------------------------------------------------------------

    def _deleteJamaFunc(self, config) :
        try :
            filename = config['filename']
            if not filename.startswith(str(conf.DIRECTORY_CONTENT_JAMA_FUNCS)) :
                os.remove(filename)
                self._wsSendCmd('JAMA-FUNC-DELETED', config)
            else :
                self._wsSendCmd('SHOW-ERROR', 'You cannot delete a Jama Func that is part of this application.')
        except :
            self._wsSendCmd('SHOW-ERROR', 'An error occurred while deleting this Jama Func.')

    # ------------------------------------------------------------------------

    def _sendAllJamaFuncsConfig(self) :
        files  = [ str(conf.DIRECTORY_CONTENT_JAMA_FUNCS  / filename) for filename in os.listdir(conf.DIRECTORY_CONTENT_JAMA_FUNCS ) ] \
               + [ str(conf.DIRECTORY_IMPORTED_JAMA_FUNCS / filename) for filename in os.listdir(conf.DIRECTORY_IMPORTED_JAMA_FUNCS) ]
        allConfig = [ ]
        self._wsSendCmd('SHOW-WAIT', 'Loading Jama Funcs...')
        for filename in files :
            if os.path.isfile(filename) and filename.upper().endswith('.PY') :
                try :
                    config = self._loadJamaFuncConfig(filename)
                    if not self._jamaFuncConfigError(config) :
                        allConfig.append(config)
                except :
                    pass
        if allConfig :
            allConfig.sort( key = lambda config: (config['info']['name'], config['info']['version']) )
            for config in allConfig :
                self._wsSendCmd('JAMA-FUNC-CONFIG', config)
        self._wsSendCmd('HIDE-WAIT')

    # ------------------------------------------------------------------------

    def _execJamaFunc(self, config, values) :
        if self._ableToUseDevice() :
            try :
                # Checks JAMA args format,
                json.dumps(values)
                # Backups and cleans globals var before JAMA code,
                code = '__gbl = globals()\n'                         + \
                       '__gblBckUp = __gbl.copy()\n'                 + \
                       'for __k in __gbl.keys() :\n'                 + \
                       '  if __k not in ("__gblBckUp", "__gbl") :\n' + \
                       '    __gbl.pop(__k)\n'                        + \
                       'if __gbl.get("__k") :\n'                     + \
                       '  del __k\n'
                # Adds JAMA args before JAMA code,
                if values :
                    code += 'class __jamaArgs() :\n'
                    for name in values :
                        value = values[name]
                        if isinstance(value, str) :
                            value = repr(value)
                        code += '  %s = %s\n' % (name, value)
                    code += '__gbl["args"] = __jamaArgs()\n'
                    code += 'del __jamaArgs\n'
                else :
                    code += '__gbl["args"] = None\n'
                # Ends clean before JAMA code,
                code += 'del __gbl\n'
                self.esp32Ctrl.ExeCodeREPL(code)
                # Adds JAMA code,
                filename = config['filename']
                with open(filename, 'rb') as f :
                    code = f.read().decode() + '\n'
                self.esp32Ctrl.ExecProgram( code         = code,
                                            codeFilename = 'JAMA-FUNC',
                                            cbProgress   = self._execJamaFuncProgress )
                self._cleanAfterJamaFunc = True
            except :
                self._wsSendCmd('HIDE-PROGRESS')
                self._wsSendCmd('EXEC-CODE-END', False)
                self._wsSendCmd('SHOW-ERROR', 'An error has occurred.')
        else :
            self._wsSendCmd('EXEC-CODE-END', False)
    
    def _execJamaFuncProgress(self, progress, size) :
        if progress < size :
            self._wsSendCmd( 'SHOW-PROGRESS',
                             dict( text    = 'Loading Jama Func into device...',
                                   percent = progress * 100 // size ) )
        else :
            self._wsSendCmd('HIDE-PROGRESS')
            self._wsSendCmd('EXEC-CODE-BEGIN')

    # ------------------------------------------------------------------------

    def _cleanAfterExecJamaFunc(self) :
        if self.esp32Ctrl and self.esp32Ctrl.IsConnected() :
            # Cleans globals var and restores it backup after JAMA code,
            code = '__gbl = globals()\n'                           + \
                   'if __gbl.get("__gblBckUp") :\n'                + \
                   '  for __k in __gbl.keys() :\n'                 + \
                   '    if __k not in ("__gblBckUp", "__gbl") :\n' + \
                   '      __gbl.pop(__k)\n'                        + \
                   '  if __gbl.get("__k") :\n'                     + \
                   '    del __k\n'                                 + \
                   '  __gbl.update(__gblBckUp)\n'                  + \
                   '  del __gblBckUp\n'                            + \
                   'del __gbl\n'
            try :
                self.esp32Ctrl.ExeCodeREPL(code)
            except :
                pass

    # ------------------------------------------------------------------------

    def _reset(self) :
        if self._ableToUseDevice() :
            try :
                self.esp32Ctrl.Reset()
                self._wsSendCmd('SHOW-ALERT', 'Resetting the device...')
            except :
                self._wsSendCmd('SHOW-ERROR', 'An error has occurred.')
        
    # ------------------------------------------------------------------------

    def _sendModules(self) :
        if self._ableToUseDevice() :
            try :
                self._wsSendCmd('MODULES', self.esp32Ctrl.GetAvailableModules())
            except :
                self._wsSendCmd('SHOW-ERROR', 'An error has occurred.')
        
    # ------------------------------------------------------------------------
    
    def _executePYFile(self, filename) :
        if self._ableToUseDevice() :
            try :
                self.esp32Ctrl.ExecutePYFile(filename)
            except :
                self._wsSendCmd('SHOW-ERROR', 'An error has occurred.')

    # ------------------------------------------------------------------------
    
    def _importModule(self, moduleName) :
        if self._ableToUseDevice() :
            try :
                self.esp32Ctrl.ImportModule(moduleName)
                self._wsSendCmd('SHOW-ALERT', 'The %s module has been imported.' % moduleName)
            except :
                self._wsSendCmd('SHOW-ERROR', 'An error has occurred.')
        
    # ------------------------------------------------------------------------

    def _installPackage(self, packageName) :
        if self._ableToUseDevice() :
            try :
                self._wsSendCmd('SHOW-WAIT', 'Attempts to download and install "%s" package...' % packageName)
                self.esp32Ctrl.InstallPackage(packageName)
                self._wsSendCmd('HIDE-WAIT')
            except :
                self._wsSendCmd('HIDE-WAIT')
                self._wsSendCmd('SHOW-ERROR', 'Unable to install "%s" package.' % packageName)

    # ------------------------------------------------------------------------

    def _setMCUFreq(self, frequency) :
        if self._ableToUseDevice() :
            try :
                if  frequency == 80 :
                    r = self.esp32Ctrl.Set80MHzFreq()
                elif frequency == 160 :
                    r = self.esp32Ctrl.Set160MHzFreq()
                elif frequency == 240 :
                    r = self.esp32Ctrl.Set240MHzFreq()
                else :
                    raise Exception()
                if r :
                    self._wsSendCmd('SYS-INFO-CHANGED')
                else :
                    self._wsSendCmd('SHOW-ERROR', 'This frequency is not supported by your device.')
            except :
                self._wsSendCmd('SHOW-ERROR', 'An error has occurred.')

    # ------------------------------------------------------------------------

    def _initSDCard(self) :
        if self._ableToUseDevice() :
            try :
                if self.esp32Ctrl.InitSDCardAndGetSize() :
                    self._sendSDCardConf()
                else :
                    self._wsSendCmd('SHOW-ERROR', 'No SD card is present.')
            except ESP32ControllerCodeException :
                self._wsSendCmd('SHOW-ERROR', 'The MicroPython port of your device does not implement SD card support.')
            except :
                self._wsSendCmd('SHOW-ERROR', 'An error has occurred.')

    # ------------------------------------------------------------------------

    def _formatSDCard(self) :
        if self._ableToUseDevice() :
            try :
                self._wsSendCmd('SHOW-WAIT', 'Format SD card...')
                if self.esp32Ctrl.FormatSDCard() :
                    self._sendSDCardConf(silence=True)
                    self._wsSendCmd('HIDE-WAIT')
                    self._wsSendCmd('SHOW-INFO', 'The SD card has been formated.')
                else :
                    self._wsSendCmd('HIDE-WAIT')
                    self._wsSendCmd('SHOW-ERROR', 'Unable to format the SD card.')
            except :
                self._wsSendCmd('HIDE-WAIT')
                self._wsSendCmd('SHOW-ERROR', 'An error has occurred.')


    # ------------------------------------------------------------------------

    def _sendSDCardConf(self, silence=False) :
        if self._ableToUseDevice(silence) :
            if not silence :
                self._wsSendCmd('SHOW-WAIT', 'Collecting informations...')
            try :
                conf = self.esp32Ctrl.GetSDCardConf()
                self._wsSendCmd('SDCARD-CONF', dict( size       = conf['size'],
                                                     mountPoint = conf['mountPoint'] )
                                               if conf else None )
                if not silence :
                    self._wsSendCmd('HIDE-WAIT')
            except :
                if not silence :
                    self._wsSendCmd('HIDE-WAIT')
                    self._wsSendCmd('SHOW-ERROR', 'An error has occurred.')

    # ------------------------------------------------------------------------
    
    def _mountSDCard(self, mountPointName) :
        if self._ableToUseDevice() :
            try :
                if self.esp32Ctrl.MountSDCardFileSystem(mountPointName) :
                    self._sendSDCardConf()
                    self._wsSendCmd('SHOW-INFO', 'The SD card has been mounted.')
                else :
                    self._wsSendCmd('SHOW-ERROR', 'The file system of the SD card cannot be mounted on the device.')
            except :
                self._wsSendCmd('SHOW-ERROR', 'An error has occurred.')

    # ------------------------------------------------------------------------

    def _umountSDCard(self) :
        if self._ableToUseDevice() :
            try :
                if self.esp32Ctrl.UmountSDCardFileSystem() :
                    self._sendSDCardConf()
                else :
                    self._wsSendCmd('SHOW-ERROR', 'Impossible to umount the file system of the SD card.')
            except :
                self._wsSendCmd('SHOW-ERROR', 'An error has occurred.')

    # ------------------------------------------------------------------------
    
    def _sendAutoInfo(self) :
        if self._ableToUseDevice(silence=True) :
            try :
                r = self.esp32Ctrl.ExeCodeREPL(   'import gc\n' \
                                                + 'try :\n' \
                                                + '  from esp32 import raw_temperature\n' \
                                                + '  rawTemp = raw_temperature()\n' \
                                                + 'except :\n' \
                                                + '  rawTemp = None\n' \
                                                + 'from time import ticks_ms\n' \
                                                + 'gc.collect()\n' \
                                                + 'print([gc.mem_alloc(), gc.mem_free(), rawTemp, ticks_ms()])\n',
                                                timeoutSec = 3 )
                info = dict( mem    = dict( alloc = r[0],
                                            free  = r[1] ),
                             temp   = dict( fahrenheit = r[2],
                                            celsius    = round(self._fahrenheit2Celsius(r[2])*10)/10 ) \
                                      if r[2] else None,
                             uptime = round(r[3] / 1000 / 60) )
                self._wsSendCmd('AUTO-INFO', info)
            except :
                pass

    # ------------------------------------------------------------------------
    
    async def _asyncAppRun(self) :
        while True :
            for i in range(conf.RECURRENT_TIMER_APP_SEC * 10) :
                await asyncio.sleep(0.100)
                if not self._appRunning :
                    return
                while (not self._wsMsgQueue.empty()) :
                    o = self._wsMsgQueue.get()
                    self._wsProcessMessage(o)
                if self._cleanAfterJamaFunc and self.esp32Ctrl and \
                   self.esp32Ctrl.IsConnected() and not self.esp32Ctrl.IsProcessing() :
                    self._cleanAfterJamaFunc = False
                    self._cleanAfterExecJamaFunc()
                    continue
            self._sendAutoInfo()
            gc.collect()

    # ------------------------------------------------------------------------

    def _appRun(self) :
        self._appRunning = True
        asyncio.run(self._asyncAppRun())

    # ------------------------------------------------------------------------

    def Start(self) :
        self._webSrv.Start(threaded=True)
        webview.start( self._appRun,
                       localization = conf.PYWEBVIEW_LOCALIZATION,
                       user_agent   = conf.APPLICATION_TITLE )
        self._appRunning = False

# ============================================================================
# ===( MAIN  )================================================================
# ============================================================================

if __name__ == '__main__' :
    try :
        os.chdir(conf.CONTENT_PATH)
        try :
            os.mkdir(conf.DIRECTORY_FILES)
        except :
            pass
        try :
            os.mkdir(conf.DIRECTORY_IMPORTED_JAMA_FUNCS)
        except :
            pass
        application = Application()
        application.Start()
    except KeyboardInterrupt :
        print('!!! KEYBOARD INTERRUPT')
    except Exception as ex :
        print('!!! INIT APP ERROR : %s' % ex)

# ============================================================================
# ============================================================================
# ============================================================================
