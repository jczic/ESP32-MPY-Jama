
# === START_CONFIG_PARAMETERS ===

dict(

    timeout         = 15,
    
    info = dict(
        name        = 'BLE iBeacon',
        version     = [1, 0, 0],
        description = 'Initializes the Bluetooth Low Energy radio and simulates an Apple iBeacon object.',
        author      = 'JC`zic',
        mail        = 'jczic.bos@gmail.com',
        www         = 'https://github.com/jczic'
    ),
    
    args = None

)

# === END_CONFIG_PARAMETERS ===


import ubluetooth
from   struct       import pack
from   binascii     import unhexlify

# ----------------------------------------------------------------------------

def _getBytesUUID(uuid) :
    if isinstance(uuid, str) :
        uuid = unhexlify(uuid.replace('-', ''))
    return (uuid if len(uuid) == 16 else None)

# ----------------------------------------------------------------------------

def _getIBeaconManufacturerData( uuid     = None,
                                 major    = 123,
                                 minor    = 456,
                                 txDBAt1M = -55 ) :
    COMPANY_ID_APPLE   = 0x004C
    IBEACON_TYPE_APPLE = 0x02
    data = _getBytesUUID(uuid)  \
         + pack('>H', major)    \
         + pack('>H', minor)    \
         + pack( 'B', txDBAt1M)
    return pack('<H', COMPANY_ID_APPLE)  \
         + pack('b', IBEACON_TYPE_APPLE) \
         + pack('b', len(data))          \
         + data

# ----------------------------------------------------------------------------

def _getAdvDataPart(dataType, dataValue) :
    return pack('BB', 1 + len(dataValue), dataType) + dataValue

# ----------------------------------------------------------------------------

def _getAdvIBeaconData() :
    boradcastFlagType    = 0x01
    manufacturedDataType = 0xFF
    brEdrNotSupported    = b'\x04'
    uuidBytes = b'B.JAMA-FUNC.TEST' # 16 bytes or str UUID mandatory
    mfData    = _getIBeaconManufacturerData(uuid=uuidBytes)
    data      = _getAdvDataPart(boradcastFlagType, brEdrNotSupported) \
              + _getAdvDataPart(manufacturedDataType, mfData)
    return data

# ----------------------------------------------------------------------------

intervalUS = 100000

try :
    ble = ubluetooth.BLE()
    ble.active(False)
    ble.active(True)
    try :
        ble.gap_advertise(None)
        ble.gap_advertise( intervalUS,
                           adv_data    = _getAdvIBeaconData(),
                           connectable = False )
        print('Ok, your device can now be found as an Apple iBeacon.')
    except :
        print('Unable to advertise the iBeacon...')
except :
    print('Unable to initialize BLE...')
