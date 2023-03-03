# ============================================================================
# ===============      This Jama Func uses a KT403A driver.    ===============
# ===============  After it, at the end, you can see the demo. ===============
# ============================================================================

# This KT403A driver was coded by JC`zic <jczic.bos@gmail.com> for MicroPython
# Files are played from a microSDcard, an USB memory or a flash memory
# 24-bit DAC output, 90 dB(at Max.) dynamic output range, signal-noise ratio at 85 dB
# Supports: MP3 and WAV audio formats on FAT16 or FAT32 files system
# Maximum supported microSD card capacity: 32 GB
# Sampling rates: 8/ 11,025 / 12 / 16 / 22,05 / 24 / 32 / 44,1 / 48 kHz
# EQ: Normal / Jazz / Classic / Pop / Rock / Bass

from machine import UART
from utime   import sleep_ms
from ustruct import unpack

class KT403AException(Exception) :
    pass

class KT403A :

    # ============================================================================
    # ===( Constants )============================================================
    # ============================================================================

    DEVICE_U_DISK = 1
    DEVICE_SD     = 2
    DEVICE_AUX    = 3
    DEVICE_SLEEP  = 4
    DEVICE_FLASH  = 5

    EQ_NORMAL     = 0
    EQ_POP        = 1
    EQ_ROCK       = 2
    EQ_JAZZ       = 3
    EQ_CLASSIC    = 4
    EQ_BASS       = 5

    # ============================================================================
    # ===( Constructor )==========================================================
    # ============================================================================

    def __init__( self,
                  uartBus,
                  txPinNum,
                  rxPinNum,
                  device    = None,
                  volume    = 70,
                  eq        = None ) :
        try :
            self._uart = UART( uartBus,
                               baudrate = 9600,
                               bits     = 8,
                               parity   = None,
                               stop     = 1,
                               tx       = txPinNum,
                               rx       = rxPinNum )
        except :
            raise KT403AException('UART bus to KT403A could not be initialized.')
        self.SetDevice(device if device else KT403A.DEVICE_SD)
        if not self.GetState() :
            raise KT403AException('KT403A could not be initialized.')
        self.SetVolume(volume)
        self.SetEqualizer(eq if eq else KT403A.EQ_NORMAL)

    # ============================================================================
    # ===( Utils )================================================================
    # ============================================================================

    def _txCmd(self, cmd, dataL=0, dataH=0) :
        self._uart.write( b'\x7E'        # Start
                        + b'\xFF'        # Firmware version
                        + b'\x06'        # Command length
                        + bytes([cmd])   # Command word
                        + b'\x00'        # Feedback flag
                        + bytes([dataH]) # DataH
                        + bytes([dataL]) # DataL
                        + b'\xEF' )      # Stop
        sleep_ms(200 if cmd == 0x09 else 1000 if cmd == 0x0C else 30)

    # ---------------------------------------------------------------------

    def _rxCmd(self) :
        if self._uart.any() :
            buf = self._uart.read(10)
            if buf              and \
               len(buf) ==   10 and \
               buf[0]   == 0x7E and \
               buf[1]   == 0xFF and \
               buf[2]   == 0x06 and \
               buf[9]   == 0xEF     :
               cmd  = buf[3]
               data = unpack('>H', buf[5:7])[0]
               return (cmd, data)
        return None

    # ----------------------------------------------------------------------------

    def _readLastCmd(self) :
        res = None
        while True :
            r = self._rxCmd()
            if not r :
                return res
            res = r

    # ============================================================================
    # ===( Functions )============================================================
    # ============================================================================

    def PlayNext(self) :
        self._txCmd(0x01)

    # ----------------------------------------------------------------------------

    def PlayPrevious(self) :
        self._txCmd(0x02)

    # ----------------------------------------------------------------------------

    def PlaySpecific(self, trackIndex) :
        self._txCmd(0x03, int(trackIndex%256), int(trackIndex/256))

    # ----------------------------------------------------------------------------

    def VolumeUp(self) :
        self._txCmd(0x04)

    # ----------------------------------------------------------------------------

    def VolumeDown(self) :
        self._txCmd(0x05)

    # ----------------------------------------------------------------------------

    def SetVolume(self, percent) :
        if percent < 0 :
            percent = 0
        elif percent > 100 :
            percent = 100
        self._txCmd(0x06, int(percent*0x1E/100))

    # ----------------------------------------------------------------------------

    def SetEqualizer(self, eq) :
        if eq < 0 or eq > 5 :
            eq = 0
        self._txCmd(0x07, eq)

    # ----------------------------------------------------------------------------

    def RepeatCurrent(self) :
        self._txCmd(0x08)

    # ----------------------------------------------------------------------------

    def SetDevice(self, device) :
        self._device = device
        self._txCmd(0x09, device)

    # ----------------------------------------------------------------------------

    def SetLowPowerOn(self) :
        self._txCmd(0x0A)

    # ----------------------------------------------------------------------------

    def SetLowPowerOff(self) :
        self.SetDevice(self._device)

    # ----------------------------------------------------------------------------

    def ResetChip(self) :
        self._txCmd(0x0C)

    # ----------------------------------------------------------------------------

    def Play(self) :
        self._txCmd(0x0D)

    # ----------------------------------------------------------------------------

    def Pause(self) :
        self._txCmd(0x0E)

    # ----------------------------------------------------------------------------

    def PlaySpecificInFolder(self, folderIndex, trackIndex) :
        self._txCmd(0x0F, trackIndex, folderIndex)

    # ----------------------------------------------------------------------------

    def EnableLoopAll(self) :
        self._txCmd(0x11, 1)

    # ----------------------------------------------------------------------------

    def DisableLoopAll(self) :
        self._txCmd(0x11, 0)

    # ----------------------------------------------------------------------------

    def PlayFolder(self, folderIndex) :
        self._txCmd(0x12, folderIndex)

    # ----------------------------------------------------------------------------

    def Stop(self) :
        self._txCmd(0x16)

    # ----------------------------------------------------------------------------

    def LoopFolder(self, folderIndex) :
        self._txCmd(0x17, folderIndex)

    # ----------------------------------------------------------------------------

    def RandomAll(self) :
        self._txCmd(0x18)

    # ----------------------------------------------------------------------------

    def EnableLoop(self) :
        self._txCmd(0x19, 0)

    # ----------------------------------------------------------------------------

    def DisableLoop(self) :
        self._txCmd(0x19, 1)

    # ----------------------------------------------------------------------------

    def EnableDAC(self) :
        self._txCmd(0x1A, 0)

    # ----------------------------------------------------------------------------

    def DisableDAC(self) :
        self._txCmd(0x1A, 1)

    # ----------------------------------------------------------------------------

    def GetState(self) :
        self._txCmd(0x42)
        r = self._readLastCmd()
        return r[1] if r and r[0] == 0x42 else None

    # ----------------------------------------------------------------------------

    def GetVolume(self) :
        self._txCmd(0x43)
        r = self._readLastCmd()
        return int(r[1] / 0x1E *100) if r and r[0] == 0x43 else 0

    # ----------------------------------------------------------------------------

    def GetEqualizer(self) :
        self._txCmd(0x44)
        r = self._readLastCmd()
        return r[1] if r and r[0] == 0x44 else 0

    # ----------------------------------------------------------------------------

    def GetFilesCount(self, device=None) :
        if not device :
            device = self._device
        if device == KT403A.DEVICE_U_DISK :
            self._txCmd(0x47)
        elif device == KT403A.DEVICE_SD :
            self._txCmd(0x48)
        elif device == KT403A.DEVICE_FLASH :
            self._txCmd(0x49)
        else :
            return 0
        sleep_ms(200)
        r = self._readLastCmd()
        return r[1] if r and r[0] >= 0x47 and r[0] <= 0x49 else 0

    # ----------------------------------------------------------------------------

    def GetFolderFilesCount(self, folderIndex) :
        self._txCmd(0x4E, folderIndex)
        sleep_ms(200)
        r = self._readLastCmd()
        return r[1] if r and r[0] == 0x4E else 0

    # ----------------------------------------------------------------------------

    def IsStopped(self) :
        return self.GetState() == 0x0200

    # ----------------------------------------------------------------------------

    def IsPlaying(self) :
        return self.GetState() == 0x0201

    # ----------------------------------------------------------------------------

    def IsPaused(self) :
        return self.GetState() == 0x0202

# ============================================================================
# =========================== End of KT403A driver ===========================
# ============================================================================


# === START_CONFIG_PARAMETERS ===

dict(

    timeout = 3,

    info    = dict(
        # ----------------------------------------------------------------------

# Supports: MP3 and WAV audio formats on FAT16 or FAT32 files system
# Maximum supported microSD card capacity: 32 GB

        name        = 'KT403A MP3 Player',
        version     = [1, 0, 0],
        description = 'For MP3 modules based on KT403A chipset like DFPlayer, Grove-MP3 v2 and more.\n'
                    + 'You will be able to connect your board via an UART bus, '
                    + 'play all the sound files in loop from the intended storage source (microSD, USB, flash memory), '
                    + 'adjust the volume but also choose an audio EQ effect (normal, pop, rock, jazz, classic, bass). '
                    + 'Info: KT403A supports MP3 & WAV audio formats on FAT16 or FAT32 files system, 32 GB max for microSD.',
        author      = 'JC`zic',
        mail        = 'jczic.bos@gmail.com',
        www         = 'https://github.com/jczic'
        # ----------------------------------------------------------------------
    ),
    
    args = dict(

        bus      = dict( label    = 'UART bus:',
                         type     = dict,
                         items    = { '1' : 'Bus 1',
                                      '2' : 'Bus 2' } ),

        txPin     = dict( label    = 'TX GPIO:',
                          type     = list ),

        rxPin     = dict( label    = 'RX GPIO:',
                          type     = list ),

        device    = dict( label    = 'Storage device source (MP3/WAV files):',
                          type     = dict,
                          items    = { '1' : 'USB stick/hd',
                                       '2' : 'microSD card',
                                       '5' : 'Flash memory' },
                          value    = '2' ),

        volume    = dict( label    = 'Volume (%):',
                          type     = int,
                          value    = 70 ),

        eq        = dict( label    = 'EQ sound effect:',
                          type     = dict,
                          items    = { '0' : 'No (normal)',
                                       '1' : 'Pop',
                                       '2' : 'Rock',
                                       '3' : 'Jazz',
                                       '4' : 'Classic',
                                       '5' : 'Bass' },
                          value    = '0' ),

    )

)

# === END_CONFIG_PARAMETERS ===


from time import sleep

kt403a = None

try :
    kt403a = KT403A( int(args.bus),
                     txPinNum = args.txPin,
                     rxPinNum = args.rxPin,
                     device   = int(args.device),
                     volume   = args.volume,
                     eq       = int(args.eq) )
    print('KT403A player initialized.')
except Exception as ex :
    print('Error: %s' % ex)
    import sys
    sys.exit()

kt403a.EnableLoopAll()

print()
print('Loop playback of all the sound files of the source...')
print('Click the red button to stop the Jama Func.')

try :
    while True :
        sleep(1)
        print('.', end='')
except KeyboardInterrupt :
    kt403a.Stop()
