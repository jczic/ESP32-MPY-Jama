# -*- coding: utf-8 -*-

# ============================================= #
#                                               #
# Copyright © 2023 JC`zic (Jean-Christophe Bos) #
#             jczic.bos@gmail.com               #
#                                               #
# ============================================= #


from   serial            import Serial
from   serial.tools      import list_ports
from   time              import sleep, time
from   os                import stat
from   binascii          import hexlify
from   _thread           import allocate_lock, start_new_thread
from   threading         import Event

# ===============================================================================

class ESP32ControllerException(Exception) :
    pass

class ESP32ControllerSerialConnException(ESP32ControllerException) :
    pass

class ESP32ControllerAlreadyProcessingException(ESP32ControllerException) :
    pass

class ESP32ControllerCodeException(ESP32ControllerException) :
    pass

# ===============================================================================

class ESP32Controller :

    # ---------------------------------------------------------------------------

    DEFAULT_CODE_FILENAME    = '<TERMINAL>'
    STDIN_CODE_FILENAME      = '<stdin>'
    KILL_AFTER_INTERRUPT_SEC = 5

    # ---------------------------------------------------------------------------

    @staticmethod
    def GetSerialPorts() :
        r = [ ]
        for port in list_ports.comports() :
            r.append( dict( Device = port.device,
                            Name   = port.name,
                            Desc   = port.description,
                            USB    = (True if port.pid else False) ) )
        return r

    # ---------------------------------------------------------------------------

    @staticmethod
    def GetFirstAvailableESP32Ctrl( baudrate          = 115200,
                                    onSerialConnError = None,
                                    onTerminalRecv    = None,
                                    onEndOfProgram    = None,
                                    onProgramError    = None,
                                    onProgramStopped  = None,
                                    onDeviceReset     = None ) :
        for port in ESP32Controller.GetSerialPorts() :
            try :
                esp32Ctrl = ESP32Controller( devicePort        = port['Device'],
                                             baudrate          = baudrate,
                                             onSerialConnError = onSerialConnError,
                                             onTerminalRecv    = onTerminalRecv,
                                             onEndOfProgram    = onEndOfProgram,
                                             onProgramError    = onProgramError,
                                             onProgramStopped  = onProgramStopped,
                                             onDeviceReset     = onDeviceReset )
                return esp32Ctrl
            except :
                pass
        return None

    # ---------------------------------------------------------------------------

    @staticmethod
    def _getWlanAuthName(authCode) :
        if   authCode == 0 :
            return 'OPEN'
        elif authCode == 1 :
            return 'WEP'
        elif authCode == 2 :
            return 'WPA-PSK'
        elif authCode == 3 :
            return 'WPA2-PSK'
        elif authCode == 4 :
            return 'WPA/WPA2-PSK'
        elif authCode == 5 :
            return 'WPA2 ENTERPRISE'
        elif authCode == 6 :
            return 'WPA3 PSK'
        elif authCode == 7 :
            return 'WPA2/WPA3 PSK'
        return 'UNKNOWN'

    # ---------------------------------------------------------------------------

    @staticmethod
    def _wlanScanToFriendlyNetworks(wlanScan) :
        networks = { }
        for x in wlanScan :
            if x[0] and not x[5] :
                ssid     = x[0].decode('UTF-8')
                rssi     = x[3]
                authCode = x[4]
                authName  = ESP32Controller._getWlanAuthName(authCode)
                if not ssid in networks :
                    networks[ssid] = dict( rssi     = rssi,
                                           authCode = authCode,
                                           authName = authName )
                elif rssi > networks[ssid]['rssi'] :
                    networks[ssid]['rssi']     = rssi
                    networks[ssid]['authCode'] = authCode
                    networks[ssid]['authName'] = authName
        sortedNetworks = sorted( networks.items(),
                                 key     = lambda item: item[1]['rssi'],
                                 reverse = True )
        return dict(sortedNetworks)

    # ---------------------------------------------------------------------------

    @staticmethod
    def _macAddrToStr(macAddr) :
        return hexlify(macAddr, ':').decode().upper()

    # ---------------------------------------------------------------------------

    @staticmethod
    def _fahrenheit2Celsius(f) :
        return (f - 32) * 5/9

    # ---------------------------------------------------------------------------

    def __init__( self,
                  devicePort,
                  baudrate          = 115200,
                  connectTimeoutSec = 3,
                  onConnProgress    = None,
                  onSerialConnError = None,
                  onTerminalRecv    = None,
                  onEndOfProgram    = None,
                  onProgramError    = None,
                  onProgramStopped  = None,
                  onDeviceReset     = None ) :

        self._devicePort         = devicePort
        self._baudrate           = baudrate
        self._onSerialConnError  = None
        self._onTerminalRecv     = onTerminalRecv
        self._onEndOfProgram     = onEndOfProgram
        self._onProgramError     = onProgramError
        self._onProgramStopped   = onProgramStopped
        self._onDeviceReset      = onDeviceReset
        self._isConnected        = False
        self._threadRunning      = False
        self._threadReading      = False
        self._inProcess          = False
        self._inCodeFileName     = None
        self._lockProcess        = allocate_lock()
        self._lockWrite          = allocate_lock()
        self._lockRead           = allocate_lock()
        self._threadReadingEvent = Event()

        try :
            self._repl = Serial( port      = devicePort,
                                 baudrate  = baudrate,
                                 timeout   = None,
                                 xonxoff   = False,
                                 exclusive = True )
            self._isConnected = True
        except :
            raise ESP32ControllerException('Cannot open serial port "%s".' % devicePort)
        
        if onConnProgress :
            onConnProgress()

        try :
            self.InterruptProgram()
            self._switchToRawMode(timeoutSec=connectTimeoutSec)
            machineNfo          = self._exeCodeREPL('import uos; [x.strip() for x in uos.uname().machine.split("with")]')
            self._machineModule = (machineNfo[0] if len(machineNfo) >= 1 else '')
            self._machineMCU    = (machineNfo[1] if len(machineNfo) >= 2 else '')
        except ESP32ControllerSerialConnException :
            raise
        except :
            raise ESP32ControllerException('The device on the "%s" port is not compatible.' % devicePort)
            
        self._onSerialConnError = onSerialConnError
        
        try :
            start_new_thread(self._threadProcess, ())
            while not self._threadRunning :
                pass
            self._threadStartReading()
        except :
            self._threadRunning = False
            raise ESP32ControllerException('Error to create an internal thread.')

    # ---------------------------------------------------------------------------

    def __del__(self) :
        self.Close(True)

    # ---------------------------------------------------------------------------

    def _threadProcess(self) :

        def cleanREPLBuffer() :
            self._switchToNormalMode()
            self._switchToRawMode()

        self._threadRunning = True
        restarted           = False
        while self._threadRunning :
            inCode = False
            b      = b''
            Event.wait(self._threadReadingEvent)
            Event.clear(self._threadReadingEvent)
            with self._lockRead :
                self._threadReading = True
                while self._threadRunning and self._threadReading :
                    try :
                        count = self._repl.in_waiting
                        if count > 0 :
                            b += self._repl.read(count)
                        if restarted :
                            if b.endswith(b'\r\n>') :
                                restarted = False
                                b = b''
                            continue
                        if len(b) >= 6 and b.endswith(b'\r\n>>> ') :
                            b = b.replace(b'\r\n>>> ', b'\r\n')
                            restarted = True
                        if not inCode and b.startswith(b'OK') :
                            inCode = True
                            b      = b[2:]
                        if inCode and len(b) >= 3 :
                            i = b.find(b'\x04>')
                            if i >= 1 :
                                if chr(b[i-1]) == '\x04' :
                                    r = b[:i-1]
                                    b = b[i+2:]
                                    if r and self._onTerminalRecv :
                                        self._onTerminalRecv(self, r.decode())
                                    cleanREPLBuffer()
                                    self._endProcess()
                                    if self._onEndOfProgram :
                                        self._onEndOfProgram(self)
                                else :
                                    i2 = b.rfind(b'\x04', 0, i)
                                    if i2 != -1 :
                                        r   = b[:i2]
                                        err = b[i2+1:i].decode()
                                        b   = b[i+2:]
                                        if r and self._onTerminalRecv :
                                            self._onTerminalRecv(self, r.decode())
                                        errMsg = err.split('\r\n')
                                        if len(errMsg) >= 3 :
                                            errFile = errMsg[-3].strip()
                                            errMsg  = errMsg[-2].strip()
                                            if errFile.find(ESP32Controller.DEFAULT_CODE_FILENAME) == -1 :
                                                if self._inCodeFileName :
                                                    errFile = errFile.replace(self.STDIN_CODE_FILENAME, '<%s>' % self._inCodeFileName)
                                                errMsg = errFile + '\r\n' + errMsg
                                        else :
                                            errMsg = err
                                        cleanREPLBuffer()
                                        self._endProcess()
                                        if errMsg.find('KeyboardInterrupt:') >= 0 :
                                            b = b''
                                            if self._onProgramStopped :
                                                self._onProgramStopped(self)
                                        elif self._onProgramError :
                                            self._onProgramError(self, errMsg)
                                inCode = False
                        if b and b.find(b'\x04') == -1 :
                            if self._onTerminalRecv :
                                self._onTerminalRecv(self, b.decode())
                            b = b''
                            if not restarted :
                                continue
                        if restarted :
                            self._endProcess()
                            self._switchToRawMode()
                            if self._onDeviceReset :
                                self._onDeviceReset(self)
                            inCode    = False
                            restarted = False
                            continue
                        sleep(0.030)
                    except :
                        self._repl.close()
                        self._threadRunning = False
                        self._isConnected   = False
                        if inCode :
                            self._endProcess()
                        if self._onSerialConnError :
                            self._onSerialConnError(self)
                if inCode :
                    self._endProcess()
                self._threadReading = False

   # ---------------------------------------------------------------------------
    
    def _endThread(self) :
        self._threadRunning = False
        with self._lockRead :
            pass

   # ---------------------------------------------------------------------------

    def _threadStartReading(self) :
        if self._threadRunning and not self._threadReading and not self._inProcess :
            Event.set(self._threadReadingEvent)
            while Event.is_set(self._threadReadingEvent) :
                pass

   # ---------------------------------------------------------------------------

    def _threadStopReading(self) :
        if self._threadReading and not self._inProcess :
            self._threadReading = False
            with self._lockRead :
                pass

   # ---------------------------------------------------------------------------

    def ExecProgram(self, code, codeFilename=None, cbProgress=None, bufSize=2048) :
        if not code :
            return
        if not self._isConnected :
            self._raiseConnectionError()
        self._beginProcess()
        if not codeFilename :
            codeFilename = ESP32Controller.DEFAULT_CODE_FILENAME
        self._inCodeFileName = codeFilename
        if code.find('\n') == -1 :
            code = 'exec(compile(%s,%s,"single"))' % (repr(code), repr(codeFilename))
        data = code.encode()
        size = len(data)
        if size :
            if cbProgress :
                cbProgress(0, size)
            progress = 0
            with self._lockWrite :
                while True :
                    try :
                        progress += self._repl.write(data[ progress : progress + bufSize ])
                        self._repl.flush()
                    except :
                        self._raiseConnectionError()
                    if cbProgress :
                        cbProgress(progress, size)
                    if progress == size :
                        try :
                            self._repl.write(b'\x04')
                            self._repl.flush()
                        except :
                            self._raiseConnectionError()
                        break

   # ---------------------------------------------------------------------------

    def InterruptProgram(self) :
        if not self._isConnected :
            self._raiseConnectionError()
        try :
            with self._lockWrite :
                self._repl.write(b'\x03\x03')
                self._repl.flush()
        except :
            self._raiseConnectionError()
        maxTime = (time() + self.KILL_AFTER_INTERRUPT_SEC)
        while self._inProcess :
            sleep(0.030)
            if time() >= maxTime :
                return False
        return True

    # ---------------------------------------------------------------------------

    def _serialReadUntil(self, endBytes, timeoutSec=1, lockRead=True) :
        if not self._isConnected :
            self._raiseConnectionError()
        if lockRead :
            self._lockRead.acquire()
        savedTimeout = self._repl.timeout
        self._repl.timeout = (timeoutSec if timeoutSec else None) 
        readErr = False
        try :
            b = self._repl.read_until(endBytes)
        except :
            readErr = True
        if lockRead :
            self._lockRead.release()
        if readErr :
            self._raiseConnectionError()
        else :
            self._repl.timeout = savedTimeout
            if not b or not b.endswith(endBytes) :
                raise ESP32ControllerException('Timeout...')
            return b.decode()

    # ---------------------------------------------------------------------------

    def _raiseConnectionError(self) :
        if self._isConnected :
            self._endThread()
            self._endProcess()
            self._repl.close()
            self._isConnected = False
            if self._onSerialConnError :
                self._onSerialConnError(self)
            raise ESP32ControllerSerialConnException('Serial connection error.')
        else :
            raise ESP32ControllerSerialConnException('Serial not connected.')

    # ---------------------------------------------------------------------------

    def _beginProcess(self) :
        with self._lockProcess :
            if self._inProcess :
                raise ESP32ControllerAlreadyProcessingException('Already processing.')
            self._inProcess = True

    # ---------------------------------------------------------------------------

    def _endProcess(self) :
        with self._lockProcess :
            self._inProcess = False

    # ---------------------------------------------------------------------------

    def _switchToRawMode(self, timeoutSec=1) :
        if not self._isConnected :
            self._raiseConnectionError()
        timeoutExists = False
        maxTime       = (time() + timeoutSec)
        while True :
            with self._lockWrite :
                self._repl.write(b'\x01')
                self._repl.flush()
            try :
                self._serialReadUntil(b'exit\r\n>', timeoutSec=0.250, lockRead=False)
                break
            except ESP32ControllerSerialConnException :
                raise
            except :
                timeoutExists = True
                if time() >= maxTime :
                    raise ESP32ControllerException('Timeout...')
        if timeoutExists :
            try :
                while True :
                    sleep(0.250)
                    x = self._repl.in_waiting
                    if x :
                        self._repl.read(x)
                    else :
                        break
            except :
                self._raiseConnectionError()

    # ---------------------------------------------------------------------------

    def _switchToNormalMode(self, timeoutSec=1) :
        if not self._isConnected :
            self._raiseConnectionError()
        try :
            with self._lockWrite :
                self._repl.write(b'\x02')
                self._repl.flush()
            self._serialReadUntil(b'\r\n>>> ', timeoutSec, lockRead=False)
        except :
            self._raiseConnectionError()

    # ---------------------------------------------------------------------------

    def Close(self, kill=False) :
        if self._isConnected :
            self._endThread()
            self._endProcess()
            if not kill :
                saveSCE = self._onSerialConnError
                self._onSerialConnError = None
                try :
                    self.InterruptProgram()
                    self._switchToNormalMode()
                except :
                    pass
                self._onSerialConnError = saveSCE
            self._repl.close()
            self._isConnected = False

    # ---------------------------------------------------------------------------

    def IsConnected(self) :
        return self._isConnected

    # ---------------------------------------------------------------------------

    def GetDeviceModule(self) :
        return self._machineModule

    # ---------------------------------------------------------------------------

    def GetDeviceMCU(self) :
        return self._machineMCU

    # ---------------------------------------------------------------------------

    def IsProcessing(self) :
        return self._inProcess

    # ---------------------------------------------------------------------------

    def GetDevicePort(self) :
        return self._devicePort

    # ---------------------------------------------------------------------------

    def _exeCodeREPL(self, code, timeoutSec=1) :
        if not code :
            return None
        if not self._isConnected :
            self._raiseConnectionError()
        if code.find('\n') == -1 :
            code = 'exec(compile(%s,"<ReplCmd>","single"))' % repr(code)
        try :
            with self._lockWrite :
                self._repl.write(code.encode() + b'\x04')
                self._repl.flush()
        except :
            self._raiseConnectionError()
        r = self._serialReadUntil(b'\x04>', timeoutSec=timeoutSec)
        if len(r) >= 5 and r.startswith('OK') :
            if r[-3] == '\x04' :
                r = r[2:-3]
                if r :
                    try :
                        return eval(r)
                    except :
                        return r
                return None
            elif r[2] == '\x04' :
                r      = r[3:-2]
                errMsg = r.split('\r\n')
                if len(errMsg) >= 2 :
                    errMsg = errMsg[-2].strip()
                else :
                    errMsg = r
                raise ESP32ControllerCodeException(errMsg)
        raise ESP32ControllerException('Data error on serial connection.')

    # ---------------------------------------------------------------------------

    def ExeCodeREPL(self, code, timeoutSec=1) :
        if not code :
            return None
        self._threadStopReading()
        self._beginProcess()
        try :
            return self._exeCodeREPL(code, timeoutSec)
        finally :
            self._endProcess()
            self._threadStartReading()

    # ---------------------------------------------------------------------------

    def _sendFile(self, localFilename, remoteFilename, cbProgress=None, bufSize=2048) :
        if not self._isConnected :
            self._raiseConnectionError()
        try :
            if cbProgress :
                fileSize = stat(localFilename)[6]
            f = open(localFilename, 'rb')
        except :
            raise ESP32ControllerException('Cannot open local file "%s"' % localFilename)
        try :
            self._exeCodeREPL('f=open(%s, "wb")' % repr(remoteFilename))
        except ESP32ControllerCodeException :
            raise ESP32ControllerException('Cannot create remote file "%s"' % remoteFilename)
        except :
            raise
        progress = 0
        while True :
            try :
                buf = f.read(bufSize)
            except :
                ESP32ControllerException('Cannot read content from local file "%s"' % localFilename)
            if not buf :
                break
            progress += len(buf)
            try :
                self._exeCodeREPL('f.write(%s)' % repr(buf), timeoutSec=3)
            except ESP32ControllerCodeException :
                raise ESP32ControllerException('Cannot write content to remote file "%s"' % remoteFilename)
            except :
                raise
            if cbProgress :
                cbProgress(progress, fileSize)
        try :
            self._exeCodeREPL('f.close()')
        except :
            pass
        f.close()

    # ---------------------------------------------------------------------------

    def _recvFile(self, remoteFilename, localFilename, cbProgress=None, bufSize=2048) :
        if not self._isConnected :
            self._raiseConnectionError()
        try :
            if cbProgress :
                self._exeCodeREPL('from uos import stat')
                fileSize = self._exeCodeREPL('stat(%s)[6]' % repr(remoteFilename))
            self._exeCodeREPL('f=open(%s, "rb")' % repr(remoteFilename))
        except ESP32ControllerCodeException :
            raise ESP32ControllerException('Cannot open remote file "%s"' % remoteFilename)
        except :
            raise
        try :
            f = open(localFilename, 'wb')
        except :
            raise ESP32ControllerException('Cannot create local file "%s"' % localFilename)
        progress = 0
        while True :
            try :
                buf = self._exeCodeREPL('f.read(%s)' % bufSize, timeoutSec=3)
            except ESP32ControllerCodeException :
                raise ESP32ControllerException('Cannot read content from remote file "%s"' % remoteFilename)
            except :
                raise
            if not buf :
                break
            progress += len(buf)
            try :
                f.write(buf)
            except :
                ESP32ControllerException('Cannot write content to local file "%s"' % localFilename)
            if cbProgress :
                cbProgress(progress, fileSize)
        f.close()
        try :
            self._exeCodeREPL('f.close()')
        except :
            pass

    # ---------------------------------------------------------------------------

    def SendFile(self, localFilename, remoteFilename, cbProgress=None, bufSize=2048
    ) :
        self._threadStopReading()
        self._beginProcess()
        try :
            self._sendFile(localFilename, remoteFilename, cbProgress, bufSize)
        finally :
            self._endProcess()
            self._threadStartReading()

    # ---------------------------------------------------------------------------

    def RecvFile(self, remoteFilename, localFilename, cbProgress=None, bufSize=2048) :
        self._threadStopReading()
        self._beginProcess()
        try :
            self._recvFile(remoteFilename, localFilename, cbProgress, bufSize)
        finally :
            self._endProcess()
            self._threadStartReading()

    # ---------------------------------------------------------------------------

    def GetFileContent(self, remoteFilename, cbProgress=None, bufSize=2048) :
        if not self._isConnected :
            self._raiseConnectionError()
        self._threadStopReading()
        self._beginProcess()
        try :
            try :
                if cbProgress :
                    self._exeCodeREPL('from uos import stat')
                    fileSize = self._exeCodeREPL('stat(%s)[6]' % repr(remoteFilename))
                    if not fileSize :
                        return
                    cbProgress(0, fileSize, b'')
                self._exeCodeREPL('f=open(%s, "rb")' % repr(remoteFilename))
            except ESP32ControllerCodeException :
                raise ESP32ControllerException('Cannot open remote file "%s"' % remoteFilename)
            except :
                raise
            content  = b''
            progress = 0
            while True :
                try :
                    buf = self._exeCodeREPL('f.read(%s)' % bufSize, timeoutSec=3)
                except ESP32ControllerCodeException :
                    raise ESP32ControllerException('Cannot read content from remote file "%s"' % remoteFilename)
                except :
                    raise
                if not buf :
                    break
                content  += buf
                progress += len(buf)
                if cbProgress :
                    cbProgress(progress, fileSize, buf)
            try :
                self._exeCodeREPL('f.close()')
            except :
                pass
            return content
        finally :
            self._endProcess()
            self._threadStartReading()

    # ---------------------------------------------------------------------------

    def PutFileContent(self, remoteFilename, contentData, cbProgress=None, bufSize=2048) :
        if not self._isConnected :
            self._raiseConnectionError()
        self._threadStopReading()
        self._beginProcess()
        try :
            try :
                self._exeCodeREPL('f=open(%s, "wb")' % repr(remoteFilename))
            except ESP32ControllerCodeException :
                raise ESP32ControllerException('Cannot create remote file "%s"' % remoteFilename)
            except :
                raise
            fileSize = len(contentData)
            if fileSize :
                if cbProgress :
                    cbProgress(0, fileSize)
                progress = 0
                while True :
                    try :
                        progress += self._exeCodeREPL('f.write(%s)' % contentData[ progress : progress + bufSize ], timeoutSec=3)
                    except ESP32ControllerCodeException :
                        raise ESP32ControllerException('Cannot write content to remote file "%s"' % remoteFilename)
                    except :
                        raise
                    if cbProgress :
                        cbProgress(progress, fileSize)
                    if progress == fileSize :
                        break
            try :
                self._exeCodeREPL('f.close()')
            except :
                pass
        finally :
            self._endProcess()
            self._threadStartReading()

    # ---------------------------------------------------------------------------

    def GetFlashRootPath(self) :
        if not self._isConnected :
            self._raiseConnectionError()
        self._threadStopReading()
        self._beginProcess()
        try :
            return self._exeCodeREPL( 'from os import getcwd\n'             +
                                      '__d = getcwd()\n'                    +
                                      'print(repr(__d[:__d.index("/")]))\n' +
                                      'del __d\n' )
        finally :
            self._endProcess()
            self._threadStartReading()

    # ---------------------------------------------------------------------------

    def GetListDir(self, path) :
        if not self._isConnected :
            self._raiseConnectionError()
        self._threadStopReading()
        self._beginProcess()
        try :
            entries = self._exeCodeREPL( 'from os import ilistdir\n' +
                                         '__ent = [ ]\n'             +
                                         '__x = None\n'              +
                                         'for __x in ilistdir(%s) :\n' % repr(path) +
                                         '  __ent.append(__x)\n'     +
                                         'print(__ent)\n'            +
                                         'del __x\n'                 +
                                         'del __ent\n',
                                         timeoutSec = 3 )
            entries.sort( key = lambda entry: (entry[1] == 0x8000) )
            r = { }
            for x in entries :
                r[x[0]] = (x[3] if x[1] == 0x8000 else None)
            return r
        finally :
            self._endProcess()
            self._threadStartReading()

    # ---------------------------------------------------------------------------

    def CreateDir(self, path) :
        if not self._isConnected :
            self._raiseConnectionError()
        self._threadStopReading()
        self._beginProcess()
        try :
            self._exeCodeREPL('from os import mkdir')
            self._exeCodeREPL('mkdir(%s)' % repr(path))
        finally :
            self._endProcess()
            self._threadStartReading()

    # ---------------------------------------------------------------------------

    def RenameFileOrDir(self, srcPath, dstPath) :
        if not self._isConnected :
            self._raiseConnectionError()
        self._threadStopReading()
        self._beginProcess()
        try :
            self._exeCodeREPL('from os import rename')
            self._exeCodeREPL('rename(%s, %s)' % (repr(srcPath), repr(dstPath)))
        finally :
            self._endProcess()
            self._threadStartReading()

    # ---------------------------------------------------------------------------

    def DeleteFileOrRecurDir(self, path) :
        if not self._isConnected :
            self._raiseConnectionError()
        self._threadStopReading()
        self._beginProcess()
        try :
            self._exeCodeREPL( 'import os\n'                         +
                               'def __rm(path) :\n'                  +
                               '  if os.stat(path)[0] == 0x8000 :\n' +
                               '    os.remove(path)\n'               +
                               '  else :\n'                          +
                               '    for f in os.listdir(path) :\n'   +
                               '      __rm(path + "/" + f)\n'        +
                               '    os.rmdir(path)\n'                +
                               '__rm(%s)\n' % repr(path)             +
                               'del __rm\n',
                               timeoutSec = 5 )
        finally :
            self._endProcess()
            self._threadStartReading()

    # ---------------------------------------------------------------------------

    def GetAvailableModules(self) :
        r = self.ExeCodeREPL('help("modules")')
        modList = [ ]
        for line in r.split('\r\n') :
            if line != 'Plus any modules on the filesystem' :
                for name in line.split() :
                    name = name.strip()
                    if name and name != '__main__' :
                        modList.append(name.replace('/', '.'))
        modList.sort()
        return modList

    # ---------------------------------------------------------------------------

    def ScanWiFiNetworks(self) :
        if not self._isConnected :
            self._raiseConnectionError()
        self._threadStopReading()
        self._beginProcess()
        try :
            self._exeCodeREPL('import network')
            self._exeCodeREPL('__w=network.WLAN(network.STA_IF)')
            active = self._exeCodeREPL('__w.active()')
            if not active :
                self._exeCodeREPL('__w.active(True)')
            wlanScan = self._exeCodeREPL('__w.scan()', timeoutSec=10)
            if not active :
                self._exeCodeREPL('__w.active(False)')
            self._exeCodeREPL('del __w')
            return self._wlanScanToFriendlyNetworks(wlanScan)
        finally :
            self._endProcess()
            self._threadStartReading()

    # ---------------------------------------------------------------------------

    def CreateWiFiStartup(self) :
        if not self._isConnected :
            self._raiseConnectionError()
        rootPath = self.GetFlashRootPath()
        self._threadStopReading()
        self._beginProcess()
        try :
            self._sendFile('esp32CtrlWiFi.py', '%s/esp32CtrlWiFi.py' % rootPath)
            self._exeCodeREPL( '_add = True\n' +
                               'try :\n' +
                               '  with open("boot.py", "r") as f :\n' +
                               '    for ln in f.readlines() :\n' +
                               '      if ln.find("esp32CtrlWiFi") >= 0 :\n' +
                               '        _add = False\n' +
                               '        break\n' +
                               'except :\n' +
                               '  pass\n' +
                               'if _add :\n' +
                               '  with open("boot.py", "a") as f :\n' +
                               '    f.write("\\nimport esp32CtrlWiFi\\n")\n' +
                               'del _add',
                               timeoutSec = 3 )
        finally :
            self._endProcess()
            self._threadStartReading()

    # ---------------------------------------------------------------------------

    def WiFiConnect(self, ssid, key=None) :
        if not self._isConnected :
            self._raiseConnectionError()
        self._threadStopReading()
        self._beginProcess()
        ok = False
        try :
            self._exeCodeREPL('import network')
            self._exeCodeREPL('from time import sleep')
            self._exeCodeREPL('__w=network.WLAN(network.STA_IF)')
            self._exeCodeREPL('__w.active(False)')
            self._exeCodeREPL('__w.active(True)')
            self._exeCodeREPL('__w.config(reconnects=2)')
            self._exeCodeREPL('__w.connect(%s, %s)' % (repr(ssid), repr(key) if key else '""'))
            self._exeCodeREPL('while __w.status() == network.STAT_CONNECTING : sleep(0.100)', timeoutSec=15)
            if self._exeCodeREPL('__w.isconnected()') :
                self._exeCodeREPL('__w.config(reconnects=-1)')
                ok = True
            else :
                self._exeCodeREPL('__w.active(False)')
            self._exeCodeREPL('del __w')
        finally :
            self._endProcess()
            self._threadStartReading()
        return ok

    # ---------------------------------------------------------------------------

    def WiFiSave(self, ssid, key=None) :
        if not self._isConnected :
            self._raiseConnectionError()
        self._threadStopReading()
        self._beginProcess()
        try :
            self._exeCodeREPL('from esp32 import NVS')
            self._exeCodeREPL('_nvs = NVS("esp32Ctrl")')
            self._exeCodeREPL('_nvs.set_blob("ssid", %s)' % repr(ssid))
            self._exeCodeREPL('_nvs.set_blob("key",  %s)' % repr(key) if key else '""')
            self._exeCodeREPL('_nvs.commit()')
            self._exeCodeREPL('del _nvs')
        finally :
            self._endProcess()
            self._threadStartReading()
        self.CreateWiFiStartup()

    # ---------------------------------------------------------------------------

    def DeleteSavedWiFi(self) :
        if not self._isConnected :
            self._raiseConnectionError()
        self._threadStopReading()
        self._beginProcess()
        try :
            self._exeCodeREPL('from esp32 import NVS')
            self._exeCodeREPL('_nvs = NVS("esp32Ctrl")')
            self._exeCodeREPL( 'try :\n' +
                               '  _nvs.erase_key("ssid")\n' +
                               '  _nvs.erase_key("key")\n' +
                               '  _nvs.commit()\n' +
                               'except :\n' +
                               '  pass' )
            self._exeCodeREPL('del _nvs')
        finally :
            self._endProcess()
            self._threadStartReading()

    # ---------------------------------------------------------------------------

    def WifiOpenAP(self, ssid, auth=None, key=None, maxcli=3) :
        if not self._isConnected :
            self._raiseConnectionError()
        if not auth :
            auth = 0
            key  = ''
        elif auth == 'WPA-PSK' :
            auth = 2
        elif auth == 'WPA2-PSK' :
            auth = 3
        elif auth == 'WPA/WPA2-PSK' :
            auth = 4
        else :
            raise ESP32ControllerException('Unknown Wi-Fi authentication type.')
        self._threadStopReading()
        self._beginProcess()
        try :
            self._exeCodeREPL('import network')
            self._exeCodeREPL('__w = network.WLAN(network.AP_IF)')
            self._exeCodeREPL('__w.active(True)')
            config = (repr(ssid), repr(auth), repr(key))
            try :
                self._exeCodeREPL('__w.config(ssid=%s, authmode=%s, password=%s)' % config)
            except :
                self._exeCodeREPL('__w.config(essid=%s, authmode=%s, password=%s)' % config)
            self._exeCodeREPL('__w.config(max_clients=%s)' % int(maxcli))
            self._exeCodeREPL('del __w')
        finally :
            self._endProcess()
            self._threadStartReading()

    # ---------------------------------------------------------------------------

    def GetWiFiActive(self, ap=False) :
        if not self._isConnected :
            self._raiseConnectionError()
        self._threadStopReading()
        self._beginProcess()
        try :
            self._exeCodeREPL('import network')
            return self._exeCodeREPL('network.WLAN(network.%s).active()' % ('AP_IF' if ap else 'STA_IF'))
        finally :
            self._endProcess()
            self._threadStartReading()

    # ---------------------------------------------------------------------------

    def CloseWiFi(self, ap=False) :
        if not self._isConnected :
            self._raiseConnectionError()
        self._threadStopReading()
        self._beginProcess()
        try :
            self._exeCodeREPL('import network')
            return self._exeCodeREPL('network.WLAN(network.%s).active(False)' % ('AP_IF' if ap else 'STA_IF'))
        finally :
            self._endProcess()
            self._threadStartReading()

    # ---------------------------------------------------------------------------

    def GetWiFiMacAddr(self, ap=False) :
        if not self._isConnected :
            self._raiseConnectionError()
        self._threadStopReading()
        self._beginProcess()
        try :
            self._exeCodeREPL('import network')
            macAddr = self._exeCodeREPL('network.WLAN(network.%s).config("mac")' % ('AP_IF' if ap else 'STA_IF'))
            return self._macAddrToStr(macAddr)
        finally :
            self._endProcess()
            self._threadStartReading()

    # ---------------------------------------------------------------------------

    def GetWiFiConfig(self, ap=False) :
        if not self._isConnected :
            self._raiseConnectionError()
        self._threadStopReading()
        self._beginProcess()
        try :
            self._exeCodeREPL('import network')
            interf = ('AP_IF' if ap else 'STA_IF')
            try :
                ssid = self._exeCodeREPL('network.WLAN(network.%s).config("ssid")' % interf)
            except :
                ssid = self._exeCodeREPL('network.WLAN(network.%s).config("essid")' % interf)
            conf = self._exeCodeREPL('network.WLAN(network.%s).ifconfig()' % interf)
            return dict( ssid    = ssid,
                         ip      = conf[0],
                         mask    = conf[1],
                         gateway = conf[2],
                         dns     = conf[3] )
        finally :
            self._endProcess()
            self._threadStartReading()

    # ---------------------------------------------------------------------------

    def GetBLEActive(self) :
        if not self._isConnected :
            self._raiseConnectionError()
        self._threadStopReading()
        self._beginProcess()
        try :
            self._exeCodeREPL('import bluetooth')
            return self._exeCodeREPL('bluetooth.BLE().active()', timeoutSec=3)
        finally :
            self._endProcess()
            self._threadStartReading()

    # ---------------------------------------------------------------------------

    def CloseBLE(self) :
        if not self._isConnected :
            self._raiseConnectionError()
        self._threadStopReading()
        self._beginProcess()
        try :
            self._exeCodeREPL('import bluetooth')
            return self._exeCodeREPL('bluetooth.BLE().active(False)', timeoutSec=3)
        finally :
            self._endProcess()
            self._threadStartReading()

    # ---------------------------------------------------------------------------

    def GetBLEMacAddr(self, ap=False) :
        if not self._isConnected :
            self._raiseConnectionError()
        self._threadStopReading()
        self._beginProcess()
        try :
            self._exeCodeREPL('import bluetooth')
            self._exeCodeREPL('__ble=bluetooth.BLE()')
            active = self._exeCodeREPL('__ble.active()')
            if not active :
                self._exeCodeREPL('__ble.active(True)', timeoutSec=3)
            macAddr = self._exeCodeREPL('__ble.config("mac")[1]')
            if not active :
                self._exeCodeREPL('__ble.active(False)', timeoutSec=3)
            self._exeCodeREPL('del __ble')
            return self._macAddrToStr(macAddr)
        finally :
            self._endProcess()
            self._threadStartReading()

    # ---------------------------------------------------------------------------

    def GetInternetOk(self) :
        if not self._isConnected :
            self._raiseConnectionError()
        self._threadStopReading()
        self._beginProcess()
        try :
            return self._exeCodeREPL( 'import network\n'                                               +
                                      'if network.WLAN(network.STA_IF).isconnected() :\n'              +
                                      '  import socket\n'                                              +
                                      '  __s = socket.socket()\n'                                      +
                                      '  try :\n'                                                      +
                                      '    __s.connect(socket.getaddrinfo("google.com", 80)[0][-1])\n' +
                                      '    __s.close()\n'                                              +
                                      '    print(True)\n'                                              +
                                      '  except :\n'                                                   +
                                      '    print(False)\n'                                             +
                                      '  del __s\n'                                                    +
                                      'else :\n'                                                       +
                                      '  print(False)\n'                                               ,
                                      timeoutSec = 7 )
        finally :
            self._endProcess()
            self._threadStartReading()



    # ---------------------------------------------------------------------------

    def GetMemInfo(self, gcCollect=False) :
        if not self._isConnected :
            self._raiseConnectionError()
        self._threadStopReading()
        self._beginProcess()
        try :
            self._exeCodeREPL('import gc')
            if gcCollect :
                self._exeCodeREPL('gc.collect()', timeoutSec=3)
            mem = self._exeCodeREPL('[gc.mem_alloc(), gc.mem_free()]')
            return dict( alloc = mem[0],
                         free  = mem[1] )
        finally :
            self._endProcess()
            self._threadStartReading()

    # ---------------------------------------------------------------------------

    def GetMCUTemp(self) :
        if not self._isConnected :
            self._raiseConnectionError()
        self._threadStopReading()
        self._beginProcess()
        try :
            self._exeCodeREPL('from esp32 import raw_temperature')
            f = self._exeCodeREPL('raw_temperature()')
            c = round(self._fahrenheit2Celsius(f)*10)/10
            return dict( fahrenheit = f,
                         celsius    = c )
        finally :
            self._endProcess()
            self._threadStartReading()

    # ---------------------------------------------------------------------------

    def GetUptimeMin(self) :
        if not self._isConnected :
            self._raiseConnectionError()
        self._threadStopReading()
        self._beginProcess()
        try :
            self._exeCodeREPL('from time import ticks_ms')
            ms = self._exeCodeREPL('ticks_ms()')
            return round(ms / 1000 / 60)
        finally :
            self._endProcess()
            self._threadStartReading()

    # ---------------------------------------------------------------------------

    def GetMHzFreq(self) :
        if not self._isConnected :
            self._raiseConnectionError()
        self._threadStopReading()
        self._beginProcess()
        try :
            self._exeCodeREPL('from machine import freq')
            return self._exeCodeREPL('freq()') // 1000000
        finally :
            self._endProcess()
            self._threadStartReading()

    # ---------------------------------------------------------------------------

    def GetFlashSize(self) :
        if not self._isConnected :
            self._raiseConnectionError()
        self._threadStopReading()
        self._beginProcess()
        try :
            self._exeCodeREPL('from esp import flash_size')
            return self._exeCodeREPL('flash_size()')
        finally :
            self._endProcess()
            self._threadStartReading()

    # ---------------------------------------------------------------------------

    def GetPlatformInfo(self) :
        if not self._isConnected :
            self._raiseConnectionError()
        self._threadStopReading()
        self._beginProcess()
        try :
            try :
                self._exeCodeREPL('import uplatform')
                platform = self._exeCodeREPL('uplatform.platform()')
            except :
                platform = 'N/A'
            self._exeCodeREPL('import uos')
            system, __, release, version, implem = self._exeCodeREPL('tuple(uos.uname())')
            self._exeCodeREPL('import sys')
            try :
                mpyVer = self._exeCodeREPL('sys.implementation.mpy')
            except :
                mpyVer = self._exeCodeREPL('sys.implementation._mpy')
            return dict( platform = platform,
                         system   = system,
                         release  = release,
                         version  = version,
                         implem   = implem,
                         spiram   = (implem.upper().find('SPIRAM') >=0),
                         mpyver   = '%s.%s' % (mpyVer & 0xff, mpyVer >> 8 & 3) )
        finally :
            self._endProcess()
            self._threadStartReading()

    # ---------------------------------------------------------------------------

    def GetPartitions(self) :
        if not self._isConnected :
            self._raiseConnectionError()
        self._threadStopReading()
        self._beginProcess()
        try :
            return self._exeCodeREPL( 'from esp32 import Partition\n' +
                                      '__p = []\n' +
                                      '__x = None\n' +
                                      'for __x in Partition.find(Partition.TYPE_APP) :\n'  +
                                      '  __p.append(__x.info())\n' +
                                      'for __x in Partition.find(Partition.TYPE_DATA) :\n' +
                                      '  __p.append(__x.info())\n' +
                                      'del __x\n'    +
                                      'print(__p)\n' +
                                      'del __p' )
        finally :
            self._endProcess()
            self._threadStartReading()

    # ---------------------------------------------------------------------------

    def GetPinsState(self) :
        if not self._isConnected :
            self._raiseConnectionError()
        self._threadStopReading()
        self._beginProcess()
        try :
            return self._exeCodeREPL( 'from machine import Pin\n'     +
                                      '__p = { }\n'                   +
                                      'for i in range(50) :\n'        +
                                      '  try :\n'                     +
                                      '    __p[i] = Pin(i).value()\n' +
                                      '  except :\n'                  +
                                      '    pass\n'                    +
                                      'print(__p)\n'                  +
                                      'del __p\n',
                                      timeoutSec = 3 )
        finally :
            self._endProcess()
            self._threadStartReading()

    # ---------------------------------------------------------------------------

    def SetFreq(self, freq) :
        if not self._isConnected :
            self._raiseConnectionError()
        self._threadStopReading()
        self._beginProcess()
        try :
            self._exeCodeREPL('from machine import freq')
            return self._exeCodeREPL( 'try :\n'               +
                                      '  freq(%s)\n' % freq   +
                                      '  print(True)\n'       +
                                      'except ValueError :\n' +
                                      '  print(False)' )
        finally :
            self._endProcess()
            self._threadStartReading()

    # ---------------------------------------------------------------------------

    def Set80MHzFreq(self) :
        return self.SetFreq(80000000)

    # ---------------------------------------------------------------------------

    def Set160MHzFreq(self) :
        return self.SetFreq(160000000)

    # ---------------------------------------------------------------------------

    def Set240MHzFreq(self) :
        return self.SetFreq(240000000)

    # ---------------------------------------------------------------------------

    def InitSDCardAndGetSize(self) :
        if not self._isConnected :
            self._raiseConnectionError()
        self._threadStopReading()
        self._beginProcess()
        try :
            self._exeCodeREPL('from machine import SDCard')
            try :
                return self._exeCodeREPL( 'try :\n'                           +
                                          '  print(__sdCard.info()[0])\n'     +
                                          'except :\n'                        +
                                          '  try :\n'                         +
                                          '    __sdCard = SDCard()\n'         +
                                          '    try :\n'                       +
                                          '      print(__sdCard.info()[0])\n' +
                                          '    except :\n'                    +
                                          '      del __sdCard\n'              +
                                          '  except :\n'                      +
                                          '      pass\n'                      +
                                          'del SDCard' )
            except :
                return None
        finally :
            self._endProcess()
            self._threadStartReading()

    # ---------------------------------------------------------------------------

    def FormatSDCard(self) :
        if not self._isConnected :
            self._raiseConnectionError()
        self._threadStopReading()
        self._beginProcess()
        try :
            return self._exeCodeREPL( 'from os import VfsFat\n'   +
                                      'try :\n'                   +
                                      '  VfsFat.mkfs(__sdCard)\n' +
                                      '  print(True)\n'           +
                                      'except :\n'                +
                                      '  print(False)\n'          +
                                      'finally :\n'               +
                                      '  del VfsFat' )
        except :
            return False
        finally :
            self._endProcess()
            self._threadStartReading()

    # ---------------------------------------------------------------------------

    def GetSDCardConf(self) :
        if not self._isConnected :
            self._raiseConnectionError()
        self._threadStopReading()
        self._beginProcess()
        try :
            size = self._exeCodeREPL('__sdCard.info()[0]')
            try :
                mountPoint = self._exeCodeREPL('__sdMountPt')
            except :
                mountPoint = None
            return dict( size = size, mountPoint = mountPoint )
        except :
            return None
        finally :
            self._endProcess()
            self._threadStartReading()

    # ---------------------------------------------------------------------------

    def MountSDCardFileSystem(self, mountPointName='/sd') :
        if not self._isConnected :
            self._raiseConnectionError()
        self._threadStopReading()
        self._beginProcess()
        try :
            return self._exeCodeREPL( 'from uos import mount\n' +
                                      'try :\n'                 +
                                      '  mount(__sdCard, %s)\n' % repr(mountPointName) +
                                      '  __sdMountPt = %s\n'    % repr(mountPointName) +
                                      '  print(True)\n'         +
                                      'except :\n'              +
                                      '  print(False)\n'        +
                                      'finally :\n'             +
                                      '  del mount' )
        except :
            return False
        finally :
            self._endProcess()
            self._threadStartReading()

    # ---------------------------------------------------------------------------

    def UmountSDCardFileSystem(self) :
        if not self._isConnected :
            self._raiseConnectionError()
        self._threadStopReading()
        self._beginProcess()
        try :
            return self._exeCodeREPL( 'from uos import umount\n' +
                                      'try :\n'                  +
                                      '  umount(__sdMountPt)\n'  +
                                      '  del __sdMountPt\n'      +
                                      '  print(True)\n'          +
                                      'except :\n'               +
                                      '  print(False)\n'         +
                                      'finally :\n'              +
                                      '  del umount' )
        except :
            return False
        finally :
            self._endProcess()
            self._threadStartReading()

    # ---------------------------------------------------------------------------

    def ReleaseSDCard(self) :
        if not self._isConnected :
            self._raiseConnectionError()
        self._threadStopReading()
        self._beginProcess()
        try :
            return self._exeCodeREPL( '__sdCard.deinit()\n' +
                                      'del __sdCard\n'      +
                                      'print(True)' )
        except :
            return False
        finally :
            self._endProcess()
            self._threadStartReading()

    # ---------------------------------------------------------------------------

    def Reset(self) :
        if not self._isConnected :
            self._raiseConnectionError()
        self._threadStopReading()
        self._beginProcess()
        try :
            self._exeCodeREPL('from machine import reset')
        finally :
            self._endProcess()
            self._threadStartReading()
        self.ExecProgram('reset()')

    # ---------------------------------------------------------------------------

    def ExecutePYFile(self, filename) :
        if not self._isConnected :
            self._raiseConnectionError()
        rfn = repr(filename)
        self.ExecProgram( 'with open(%s, "r") as __f :\n'           % rfn +
                          '  exec(compile(__f.read(),%s,"exec"))\n' % rfn )

    # ---------------------------------------------------------------------------

    def ImportModule(self, moduleName) :
        if not self._isConnected :
            self._raiseConnectionError()
        self._threadStopReading()
        self._beginProcess()
        try :
            self._exeCodeREPL('import %s' % moduleName, timeoutSec=7)
        finally :
            self._endProcess()
            self._threadStartReading()

    # ---------------------------------------------------------------------------

    def InstallPackage(self, packageName) :
        if not self._isConnected :
            self._raiseConnectionError()
        self._threadStopReading()
        self._beginProcess()
        try :
            try :
                self._exeCodeREPL('import mip', timeoutSec=3)
                module = 'mip'
            except :
                self._exeCodeREPL('import upip', timeoutSec=3)
                module = 'upip'
            try :
                r = self._exeCodeREPL('%s.install(%s)' % (module, repr(packageName)), timeoutSec=None)
            except Exception as ex :
                if self._onTerminalRecv :
                    self._onTerminalRecv(self, 'Unable to install package (is Wi-Fi/Internet connected?)\n\n')
                raise ex
            if r and self._onTerminalRecv :
                self._onTerminalRecv(self, str(r) + '\n')
        finally :
            self._endProcess()
            self._threadStartReading()

# ===============================================================================
