
# Jama Func at the end of code.


# ============================================================================
# ===( BLEAdvReader )=========================================================
# ============================================================================

"""
BLEAdvReader from https://github.com/jczic/BLEAdvReader (MIT)
"""

from ustruct   import pack, unpack
from ubinascii import hexlify

class BLEAdvReader :

    # ============================================================================
    # ===( Constants )============================================================
    # ============================================================================

    DATA_TYPE_FLAGS                 = 0x01
    DATA_TYPE_INCOMP_16BITS_UUIDS   = 0x02
    DATA_TYPE_COMP_16BITS_UUIDS     = 0x03
    DATA_TYPE_INCOMP_32BITS_UUIDS   = 0x04
    DATA_TYPE_COMP_32BITS_UUIDS     = 0x05
    DATA_TYPE_INCOMP_128BITS_UUIDS  = 0x06
    DATA_TYPE_COMP_128BITS_UUIDS    = 0x07
    DATA_TYPE_SHORT_NAME            = 0x08
    DATA_TYPE_COMPLETE_NAME         = 0x09
    DATA_TYPE_TX_POWER_LEVEL        = 0x0A
    DATA_TYPE_DEVICE_CLASS          = 0x0B
    DATA_TYPE_SMP_PAIR_HASH_C       = 0x0C
    DATA_TYPE_SMP_PAIR_HASH_C192    = 0x0D
    DATA_TYPE_SMP_PAIR_RAND_R       = 0x0E
    DATA_TYPE_SMP_PAIR_RAND_R192    = 0x0F
    DATA_TYPE_DEVICE_ID             = 0x10
    DATA_TYPE_SECU_MNGR_TK_VAL      = 0x11
    DATA_TYPE_SECU_MNGR_OOB_FLAGS   = 0x12
    DATA_TYPE_SLAVE_CONN_INT_RNG    = 0x13
    DATA_TYPE_16BITS_SVC_SOL_UUIDS  = 0x14
    DATA_TYPE_128BITS_SVC_SOL_UUIDS = 0x15
    DATA_TYPE_SVC_DATA              = 0x16
    DATA_TYPE_SVC_DATA_16BITS_UUID  = 0x17
    DATA_TYPE_PUB_TARGET_ADDR       = 0x18
    DATA_TYPE_RAND_TARGET_ADDR      = 0x19
    DATA_TYPE_APPEARANCE            = 0x1A
    DATA_TYPE_ADV_INT               = 0x1B
    DATA_TYPE_LE_BLT_DEVICE_ADDR    = 0x1C
    DATA_TYPE_LE_ROLE               = 0x1D
    DATA_TYPE_SMP_PAIR_HASH_C256    = 0x1E
    DATA_TYPE_SMP_PAIR_RAND_R256    = 0x1F
    DATA_TYPE_32BITS_SVC_SOL_UUIDS  = 0x20
    DATA_TYPE_SVC_DATA_32BITS_UUID  = 0x21
    DATA_TYPE_SVC_DATA_128BITS_UUID = 0x22
    DATA_TYPE_LE_SECU_CONN_RAND_VAL = 0x23
    DATA_TYPE_URI                   = 0x24
    DATA_TYPE_INDOOR_POS            = 0x25
    DATA_TYPE_TRANS_DISCOV_DATA     = 0x26
    DATA_TYPE_LE_SUPPORT_FEAT       = 0x27
    DATA_TYPE_CHAN_MAP_UPD_INDIC    = 0x28
    DATA_TYPE_PB_ADV                = 0x29
    DATA_TYPE_MESH_MSG              = 0x2A
    DATA_TYPE_MESH_BEACON           = 0x2B
    DATA_TYPE_3D_INFO_DATA          = 0x3D
    DATA_TYPE_MANUFACTURER_DATA     = 0xFF

    MEMBER_UUID_GOOGLE_EDDYSTONE    = 0xFEAA

    COMPANY_ID_APPLE                = 0x004C

    APPLE_TYPE_IBEACON              = 0x02
    APPLE_TYPE_AIRDROP              = 0x05
    APPLE_TYPE_AIRPODS              = 0x07
    APPLE_TYPE_AIRPLAY_DEST         = 0x09
    APPLE_TYPE_AIRPLAY_SRC          = 0x0A
    APPLE_TYPE_HANDOFF              = 0x0C
    APPLE_TYPE_NEARBY               = 0x10

    # ============================================================================
    # ===( Class InvalidAdvData )=================================================
    # ============================================================================

    class InvalidAdvData(Exception) :
        pass

    # ============================================================================
    # ===( Constructor )==========================================================
    # ============================================================================

    def __init__(self, advertisingData) :
        self._advData = dict()
        self._advObj  = [ ]
        self._advDataProcess(advertisingData)
        self._advDataElementsProcess()
        self._advKnownElementsProcess()

    # ============================================================================
    # ===( Functions )============================================================
    # ============================================================================

    @staticmethod
    def _hex(data) :
        if data :
            return hexlify(data).decode().upper()
        return ''

    # ----------------------------------------------------------------------------

    @staticmethod
    def _twosComp(val, bits) :
        if val < 2**bits :
            return val - int((val << 1) & 2**bits)
        raise ValueError('Value %s out of range of %s-bit value.' % (val, bits))

    # ----------------------------------------------------------------------------

    @staticmethod
    def _accum88(data16b) :
        if isinstance(data16b, bytes) and len(data16b) == 2 :
            return BLEAdvReader._twosComp(data16b[0],  8) + \
                   BLEAdvReader._twosComp(data16b[1], 16) / 256
        raise ValueError('%s is not a 16 bits data value.' % data16b)

    # ----------------------------------------------------------------------------

    @staticmethod
    def _128bitsUUID(uuidBytes) :
        if uuidBytes and len(uuidBytes) == 16 :
            s = hexlify(uuidBytes).decode()
            return s[:8] + '-' + s[8:12] + '-' + s[12:16] + '-' + s[16:20] + '-' + s[20:]
        return ''

    # ----------------------------------------------------------------------------

    @staticmethod
    def _decodeURIBeacon(data) :
        schemes = {
            0x00 : 'http://www.',   0x01 : 'https://www.',
            0x02 : 'http://',       0x03 : 'https://'
        }
        expansions = {
            0x00 : '.com/',  0x01 : '.org/', 0x02 : '.edu/', 0x03 : '.net/',
            0x04 : '.info/', 0x05 : '.biz/', 0x06 : '.gov/', 0x07 : '.com',
            0x08 : '.org',   0x09 : '.edu',  0x0A : '.net',
            0x0B : '.info',  0x0C : '.biz',  0x0D : '.gov'
        }
        try :
            url = schemes[data[0]]
            for b in data[1:] :
                url += expansions[b] if b in expansions else chr(b)
            return url
        except :
            return ''

    # ----------------------------------------------------------------------------

    def _advDataProcess(self, advData) :
        if advData :
            advDataLen = len(advData)
            idx        = 0
            while idx < advDataLen :
                dataLen  = advData[idx]
                idx     += 1
                if dataLen > 0 :
                    idxEnd = idx + dataLen
                    if idxEnd <= advDataLen :
                        dataType = advData[idx]
                        data     = advData[idx+1:idxEnd]
                        self._advData[dataType] = data
                    else :
                        raise self.InvalidAdvData('Data element invalid size')
                    idx = idxEnd

    # ----------------------------------------------------------------------------

    def _advDataElementsProcess(self) :
        if not self._advData :
            raise self.InvalidAdvData('No advertising data element')
        for dataType in self._advData :
            data   = self._advData[dataType]
            advObj = None
            if dataType == self.DATA_TYPE_FLAGS :
                try :
                    advObj = self.Flags(ord(data))
                except :
                    raise self.InvalidAdvData('Invalid flags data element')
            elif dataType == self.DATA_TYPE_COMP_16BITS_UUIDS :
                try :
                    advObj = self.AdoptedService16bits(unpack('<H', data)[0])
                except :
                    raise self.InvalidAdvData('Invalid adopted service 16bits data element')
            elif dataType == self.DATA_TYPE_COMP_32BITS_UUIDS :
                try :
                    advObj = self.AdoptedService32bits(unpack('<I', data)[0])
                except :
                    raise self.InvalidAdvData('Invalid adopted service 32bits data element')
            elif dataType == self.DATA_TYPE_COMP_128BITS_UUIDS :
                try :
                    advObj = self.AdoptedService128bits(data)
                except :
                    raise self.InvalidAdvData('Invalid adopted service 128bits data element')
            elif dataType == self.DATA_TYPE_SHORT_NAME :
                try :
                    advObj = self.ShortName(data.decode())
                except :
                    raise self.InvalidAdvData('Invalid short name data element')
            elif dataType == self.DATA_TYPE_COMPLETE_NAME :
                try :
                    advObj = self.CompleteName(data.decode())
                except :
                    raise self.InvalidAdvData('Invalid complete name data element')
            elif dataType == self.DATA_TYPE_TX_POWER_LEVEL :
                try :
                    advObj = self.TXPowerLevel(unpack('<b', data)[0])
                except :
                    raise self.InvalidAdvData('Invalid TX power level data element')
            elif dataType == self.DATA_TYPE_SVC_DATA :
                try :
                    advObj = self.ServiceData(unpack('<H', data[0:2])[0], data[2:])
                except :
                    raise self.InvalidAdvData('Invalid service data element')
            elif dataType == self.DATA_TYPE_MANUFACTURER_DATA :
                try :
                    advObj = self.ManufacturerData(unpack('<H', data[0:2])[0], data[2:])
                except :
                    raise self.InvalidAdvData('Invalid manufacturer data element')
            if advObj :
                self._advObj.append(advObj)

    # ----------------------------------------------------------------------------

    def _advKnownElementsProcess(self) :
        for advObj in self._advObj :
            if isinstance(advObj, self.AdoptedService16bits) :
                if advObj.UUID == self.MEMBER_UUID_GOOGLE_EDDYSTONE :
                    try :
                        advObjToAdd = None
                        for ao in self._advObj :
                            if isinstance(ao, self.ServiceData) and \
                               ao.UUID == self.MEMBER_UUID_GOOGLE_EDDYSTONE :
                                advObjToAdd = self._getAdvObjForGoogleEddyStoneData(ao.Data)
                                break
                        if advObjToAdd :
                            self._advObj.append(advObjToAdd)
                        else :
                            raise Exception()
                    except :
                        raise self.InvalidAdvData('Invalid Google EddyStone data')
            elif isinstance(advObj, self.ManufacturerData) :
                if advObj.CompanyID == self.COMPANY_ID_APPLE :
                    try :
                        advObjToAdd = self._getAdvObjForAppleCompanyData(advObj.Data)
                        if advObjToAdd :
                            self._advObj.append(advObjToAdd)
                        else :
                            raise Exception()
                    except :
                        raise self.InvalidAdvData('Invalid Apple manufacturer data')

    # ----------------------------------------------------------------------------

    def _getAdvObjForAppleCompanyData(self, data) :
        appleType = data[0]
        dataLen   = data[1]
        data      = data[2:]
        if appleType == self.APPLE_TYPE_IBEACON :
            return self.AppleIBeacon( data[:16],
                                      unpack('>H', data[16:18])[0],
                                      unpack('>H', data[18:20])[0],
                                      data[20] - 256 )
        elif appleType == self.APPLE_TYPE_AIRDROP :
            return self.AppleService('AirDrop', data)
        elif appleType == self.APPLE_TYPE_AIRPODS :
            return self.AppleService('AirPods', data)
        elif appleType == self.APPLE_TYPE_AIRPLAY_DEST :
            return self.AppleService('AirPlay Destination', data)
        elif appleType == self.APPLE_TYPE_AIRPLAY_SRC :
            return self.AppleService('AirPlay Source', data)
        elif appleType == self.APPLE_TYPE_HANDOFF :
            return self.AppleService('HandOff', data)
        elif appleType == self.APPLE_TYPE_NEARBY :
            return self.AppleService('Nearby', data)
        return self.AppleService()

    # ----------------------------------------------------------------------------

    def _getAdvObjForGoogleEddyStoneData(self, data) :
        frameType = data[0]
        if frameType == 0x00 :
            txPower   = unpack('<b', bytes([data[1]]))[0]
            namespace = data[2:12]
            instance  = data[12:18]
            return self.EddyStoneUID(txPower, namespace, instance)
        elif frameType == 0x10 :
            txPower = unpack('<b', bytes([data[1]]))[0]
            url     = self._decodeURIBeacon(data[2:])
            return self.EddyStoneURL(txPower, url)
        elif frameType == 0x20 :
            version = data[1]
            if version == 0x00 :
                vbatt  = unpack('>H', data[2:4])[0]
                temp   = BLEAdvReader._accum88(data[4:6])
                advCnt = unpack('>I', data[6:10])[0]
                secCnt = unpack('>I', data[10:14])[0]
                return self.EddyStoneTLMUnencrypted(vbatt, temp, advCnt, secCnt)
            elif version == 0x01 :
                etlm = data[2:14]
                salt = unpack('>H', data[14:16])[0]
                mic  = unpack('>H', data[16:18])[0]
                return self.EddyStoneTLMEncrypted(etlm, salt, mic)
        elif frameType == 0x30 :
            txPower     = unpack('<b', bytes([data[1]]))[0]
            encryptedID = data[2:10]
            return self.EddyStoneEID(txPower, encryptedID)
        return None

    # ----------------------------------------------------------------------------

    def GetDataByDataType(self, dataType) :
        return self._advData.get(dataType)

    # ----------------------------------------------------------------------------

    def GetAllElements(self) :
        return self._advObj

    # ----------------------------------------------------------------------------

    def GetElementByClass(self, elementType) :
        for advObj in self._advObj :
            if isinstance(advObj, elementType) :
                return advObj
        return None

    # ============================================================================
    # ===( Class Flags )==========================================================
    # ============================================================================

    class Flags :

        FLAG_LE_LIMITED_DISC_MODE       = 0x01
        FLAG_LE_GENERAL_DISC_MODE       = 0x02
        FLAG_BR_EDR_NOT_SUPPORTED       = 0x04
        FLAG_LE_BR_EDR_CONTROLLER       = 0x08
        FLAG_LE_BR_EDR_HOST             = 0x10
        FLAGS_LE_ONLY_LIMITED_DISC_MODE = 0x01 | 0x04
        FLAGS_LE_ONLY_GENERAL_DISC_MODE = 0x02 | 0x04

        def __init__(self, flags=0x00) :
            self._flags = flags

        def __str__(self) :
            return '{0:08b}'.format(self._flags)

        @property
        def LE_LIMITED_DISC_MODE(self) :
            return bool(self._flags & self.FLAG_LE_LIMITED_DISC_MODE)

        @property
        def LE_GENERAL_DISC_MODE(self) :
            return bool(self._flags & self.FLAG_LE_GENERAL_DISC_MODE)

        @property
        def BR_EDR_NOT_SUPPORTED(self) :
            return bool(self._flags & self.FLAG_BR_EDR_NOT_SUPPORTED)

        @property
        def LE_BR_EDR_CONTROLLER(self) :
            return bool(self._flags & self.FLAG_LE_BR_EDR_CONTROLLER)

        @property
        def LE_BR_EDR_HOST(self) :
            return bool(self._flags & self.FLAG_LE_BR_EDR_HOST)

        @property
        def LE_ONLY_LIMITED_DISC_MODE(self) :
            return bool(self._flags & self.FLAGS_LE_ONLY_LIMITED_DISC_MODE)

        @property
        def LE_ONLY_GENERAL_DISC_MODE(self) :
            return bool(self._flags & self.FLAGS_LE_ONLY_GENERAL_DISC_MODE)

    # ============================================================================
    # ===( Class AdoptedService16bits )===========================================
    # ============================================================================

    class AdoptedService16bits :

        def __init__(self, svcUUID=0x0000) :
            self._svcUUID = svcUUID

        def __str__(self) :
            return 'Adopted Service (16bits UUID=%s)' % self.StrUUID

        @property
        def UUID(self) :
            return self._svcUUID

        @property
        def StrUUID(self) :
            return BLEAdvReader._hex(pack('<H', self._svcUUID))

    # ============================================================================
    # ===( Class AdoptedService32bits )===========================================
    # ============================================================================

    class AdoptedService32bits :

        def __init__(self, svcUUID=0x00000000) :
            self._svcUUID = svcUUID

        def __str__(self) :
            return 'Adopted Service (32bits UUID=%s)' % self.StrUUID

        @property
        def UUID(self) :
            return self._svcUUID

        @property
        def StrUUID(self) :
            return BLEAdvReader._hex(pack('<I', self._svcUUID))

    # ============================================================================
    # ===( Class AdoptedService128bits )==========================================
    # ============================================================================

    class AdoptedService128bits :

        def __init__(self, svcUUID=b'') :
            self._svcUUID = svcUUID

        def __str__(self) :
            return 'Adopted Service (128bits UUID=%s)' % self.StrUUID

        @property
        def UUID(self) :
            return self._svcUUID

        @property
        def StrUUID(self) :
            return BLEAdvReader._128bitsUUID(self._svcUUID)

    # ============================================================================
    # ===( Class ShortName )======================================================
    # ============================================================================

    class ShortName :

        def __init__(self, shortName='') :
            self._shortName = shortName

        def __str__(self) :
            return self._shortName

    # ============================================================================
    # ===( Class CompleteName )===================================================
    # ============================================================================

    class CompleteName :

        def __init__(self, completeName='') :
            self._completeName = completeName

        def __str__(self) :
            return self._completeName

    # ============================================================================
    # ===( Class TXPowerLevel )===================================================
    # ============================================================================

    class TXPowerLevel :

        def __init__(self, txPowerLvl=0) :
            self._txPowerLvl= txPowerLvl

        def __str__(self) :
            return '%sdBm' % self._txPowerLvl

        def GetProximityByLogTX(self, rssi, n_PathLossExp=2) :
            return BLEAdvReader.ProximityHelper. \
                   LogTX(rssi, self._txPowerLvl, n_PathLossExp)

        def GetProximityByOldBconTX(self, rssi) :
            return BLEAdvReader.ProximityHelper. \
                   OldBconTX(rssi, self._txPowerLvl)

        def GetProximityByNewBconTX(self, rssi) :
            return BLEAdvReader.ProximityHelper. \
                   NewBconTX(rssi, self._txPowerLvl)

        @property
        def DBM(self) :
            return self._txPowerLvl

    # ============================================================================
    # ===( Class ServiceData )====================================================
    # ============================================================================

    class ServiceData :

        def __init__(self, uuid16bits=0x0000, data=b'') :
            self._uuid16bits = uuid16bits
            self._data       = data

        def __str__(self) :
            return 'Service data of UUID %s (%s)' % ( self.StrUUID,
                                                      BLEAdvReader._hex(self._data) )

        @property
        def UUID(self) :
            return self._uuid16bits

        @property
        def StrUUID(self) :
            return BLEAdvReader._hex(pack('<H', self._uuid16bits))

        @property
        def Data(self) :
            return self._data

    # ============================================================================
    # ===( Class ManufacturerData )===============================================
    # ============================================================================

    class ManufacturerData :

        def __init__(self, companyID=0x0000, data=b'') :
            self._companyID = companyID
            self._data      = data

        def __str__(self) :
            return 'Manufacturer data from company %s (%s)' % ( self.StrCompanyID,
                                                                BLEAdvReader._hex(self._data) )

        @property
        def CompanyID(self) :
            return self._companyID

        @property
        def StrCompanyID(self) :
            return BLEAdvReader._hex(pack('<H', self._companyID))

        @property
        def Data(self) :
            return self._data

    # ============================================================================
    # ===( Class AppleService )===================================================
    # ============================================================================

    class AppleService :

        def __init__(self, typeName='', data=b'') :
            self._typeName = typeName
            self._data     = data

        def __str__(self) :
            if self._typeName :
                return 'Apple Service %s (%s)' % ( self._typeName,
                                                   BLEAdvReader._hex(self._data) )
            return 'Unknown Apple Service'

        @property
        def TypeName(self) :
            return self._typeName

        @property
        def Data(self) :
            return self._data

    # ============================================================================
    # ===( Class AppleIBeacon )===================================================
    # ============================================================================

    class AppleIBeacon :

        def __init__(self, uuid=None, major=0, minor=0, txPower=-1) :
            self._uuid    = uuid
            self._major   = major
            self._minor   = minor
            self._txPower = txPower

        def __str__(self) :
            return 'Apple iBeacon %s, %s.%s, %sdBm' % ( self.StrUUID,
                                                        self._major,
                                                        self._minor,
                                                        self._txPower )

        def GetProximityByLogTX(self, rssi, n_PathLossExp=2) :
            return BLEAdvReader.ProximityHelper. \
                   LogTX(rssi, self._txPower, n_PathLossExp)

        def GetProximityByOldBconTX(self, rssi) :
            return BLEAdvReader.ProximityHelper. \
                   OldBconTX(rssi, self._txPower)

        def GetProximityByNewBconTX(self, rssi) :
            return BLEAdvReader.ProximityHelper. \
                   NewBconTX(rssi, self._txPower)

        @property
        def UUID(self) :
            return self._uuid

        @property
        def StrUUID(self) :
            return BLEAdvReader._128bitsUUID(self._uuid)

        @property
        def Major(self) :
            return self._major

        @property
        def Minor(self) :
            return self._minor

        @property
        def TxPower(self) :
            return self._txPower

    # ============================================================================
    # ===( Class EddyStoneUID )===================================================
    # ============================================================================

    class EddyStoneUID :

        def __init__(self, txPower=-1, namespace=b'', instance=b'') :
            self._txPower   = txPower
            self._namespace = namespace
            self._instance  = instance

        def __str__(self) :
            return 'EddyStone UID %sdBm, %s, %s' % ( self._txPower,
                                                     BLEAdvReader._hex(self._namespace),
                                                     BLEAdvReader._hex(self._instance) )

        def GetProximityByLogTX(self, rssi, n_PathLossExp=2) :
            return BLEAdvReader.ProximityHelper. \
                   LogTX(rssi, self._txPower, n_PathLossExp)

        def GetProximityByOldBconTX(self, rssi) :
            return BLEAdvReader.ProximityHelper. \
                   OldBconTX(rssi, self._txPower)

        def GetProximityByNewBconTX(self, rssi) :
            return BLEAdvReader.ProximityHelper. \
                   NewBconTX(rssi, self._txPower)

        @property
        def TxPower(self) :
            return self._txPower

        @property
        def Namespace(self) :
            return self._namespace

        @property
        def Instance(self) :
            return self._instance

    # ============================================================================
    # ===( Class EddyStoneURL )===================================================
    # ============================================================================

    class EddyStoneURL :

        def __init__(self, txPower=-1, url='') :
            self._txPower = txPower
            self._url     = url

        def __str__(self) :
            return 'EddyStone URL %sdBm, %s' % (self._txPower, self._url)

        def GetProximityByLogTX(self, rssi, n_PathLossExp=2) :
            return BLEAdvReader.ProximityHelper. \
                   LogTX(rssi, self._txPower, n_PathLossExp)

        def GetProximityByOldBconTX(self, rssi) :
            return BLEAdvReader.ProximityHelper. \
                   OldBconTX(rssi, self._txPower)

        def GetProximityByNewBconTX(self, rssi) :
            return BLEAdvReader.ProximityHelper. \
                   NewBconTX(rssi, self._txPower)

        @property
        def TxPower(self) :
            return self._txPower

        @property
        def URL(self) :
            return self._url

    # ============================================================================
    # ===( Class EddyStoneTLMUnencrypted )==========================================
    # ============================================================================

    class EddyStoneTLMUnencrypted :

        def __init__(self, vbatt=0, temp=0, advCnt=0, secCnt=0) :
            self._vbatt  = vbatt
            self._temp   = temp
            self._advCnt = advCnt
            self._secCnt = secCnt

        def __str__(self) :
            return 'EddyStone TLM Unencrypted %smV, %s°C, %s, %s' % ( self._vbatt,
                                                                      self._temp,
                                                                      self._advCnt,
                                                                      self._secCnt )

        @property
        def VBatt(self) :
            return self._vbatt

        @property
        def Temp(self) :
            return self._temp

        @property
        def AdvCnt(self) :
            return self._advCnt

        @property
        def SecCnt(self) :
            return self._secCnt

    # ============================================================================
    # ===( Class EddyStoneTLMEncrypted )==========================================
    # ============================================================================

    class EddyStoneTLMEncrypted :

        def __init__(self, etlm=b'', salt=0, mic=0) :
            self._etlm = etlm
            self._salt = salt
            self._mic  = mic

        def __str__(self) :
            return 'EddyStone TLM Encrypted %s, %s, %s' % ( BLEAdvReader._hex(self._etlm),
                                                            self._salt,
                                                            self._mic )

        @property
        def ETLM(self) :
            return self._etlm

        @property
        def SALT(self) :
            return self._salt

        @property
        def MIC(self) :
            return self._mic

    # ============================================================================
    # ===( Class EddyStoneEID )===================================================
    # ============================================================================

    class EddyStoneEID :

        def __init__(self, txPower=-1, encryptedID=b'') :
            self._txPower     = txPower
            self._encryptedID = encryptedID

        def __str__(self) :
            return 'EddyStone EID %sdBm, %s' % ( self._txPower,
                                                 BLEAdvReader._hex(self._encryptedID) )

        def GetProximityByLogTX(self, rssi, n_PathLossExp=2) :
            return BLEAdvReader.ProximityHelper. \
                   LogTX(rssi, self._txPower, n_PathLossExp)

        def GetProximityByOldBconTX(self, rssi) :
            return BLEAdvReader.ProximityHelper. \
                   OldBconTX(rssi, self._txPower)

        def GetProximityByNewBconTX(self, rssi) :
            return BLEAdvReader.ProximityHelper. \
                   NewBconTX(rssi, self._txPower)

        @property
        def TxPower(self) :
            return self._txPower

        @property
        def EncryptedID(self) :
            return self._encryptedID

    # ============================================================================
    # ===( Class ProximityHelper )================================================
    # ============================================================================

    class ProximityHelper :

        @staticmethod
        def _txFormula(A, B, C, r, t) :
            return A * ( (r/t) ** B ) + C

        @staticmethod
        def LogTX(rssi, rssiTX, n_PathLossExp=2) :
            return 10.0 ** ( (rssi-rssiTX) / (-10*n_PathLossExp) )

        @staticmethod
        def OldBconTX(rssi, rssiTX) :
            return BLEAdvReader.ProximityHelper. \
                   _txFormula(0.89976, 7.7095, 0.111, rssi, rssiTX)

        @staticmethod
        def NewBconTX(rssi, rssiTX) :
            return BLEAdvReader.ProximityHelper. \
                   _txFormula(0.42093, 6.9476, 0.54992, rssi, rssiTX)

# ============================================================================
# ============================================================================
# ============================================================================


# === START_CONFIG_PARAMETERS ===

dict(

    timeout         = 15,
    
    info = dict(
        name        = 'BLE Scan',
        version     = [1, 0, 0],
        description = 'Initializes the Bluetooth Low Energy radio and scans BLE devices via advertising data.',
        author      = 'JC`zic',
        mail        = 'jczic.bos@gmail.com',
        www         = 'https://github.com/jczic'
    ),
    
    args = None

)

# === END_CONFIG_PARAMETERS ===


import bluetooth
from   ubinascii import hexlify
from   time      import sleep

def mac2str(mac) :
    if mac :
        return hexlify(mac, ':').decode().upper()
    return ''

_IRQ_SCAN_RESULT = 5
_IRQ_SCAN_DONE   = 6

_process = False
_bleAdv  = { }

def _bleIRQ(event, data) :
    if event == _IRQ_SCAN_RESULT :
        addr_type, addr, adv_type, rssi, adv_data = data
        _bleAdv[mac2str(addr)] = [ rssi, bytes(adv_data) ]
    elif event == _IRQ_SCAN_DONE :
        global _process
        _process = False

ble = bluetooth.BLE()

if ble.active() :
    print('BLE is already active on the device: end of Jama Func for security.')
    import sys
    sys.exit()

ble.active(True)
ble.irq(_bleIRQ)

_process = True
ble.gap_scan(7000, 1000000, 50000, False)
print('Scanning BLE...', end='')

while _process :
    sleep(1)
    print('.', end='')
print('\n')

for mac in _bleAdv :
    print('>> MAC %s (rssi %sdBm)' % (mac, _bleAdv[mac][0]))
    try :
        r = BLEAdvReader(_bleAdv[mac][1])
        for advObj in r.GetAllElements() :
            print('   - %s: %s' % (type(advObj).__name__, advObj))
    except :
        pass
    print()

print('Ok, %s found.' % len(_bleAdv))

ble.active(False)

