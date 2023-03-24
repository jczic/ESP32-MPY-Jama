
# === START_CONFIG_PARAMETERS ===

dict(

    timeout         = 15,
    
    info = dict(
        name        = 'Wi-Fi Scan',
        version     = [1, 0, 0],
        description = 'Performs a detailed scan of the wireless access points.',
        author      = 'JC`zic',
        mail        = 'jczic.bos@gmail.com',
        www         = 'https://github.com/jczic'
    ),

    args = None

)

# === END_CONFIG_PARAMETERS ===

from   binascii import hexlify
import network

# ------------------------------------------------------------------------------------

def _macAddrFromBSSID(bssid) :
    return hexlify(bssid, ':').decode().upper()

# ------------------------------------------------------------------------------------

def _signalStrengthFromRSSI(rssi) :
    return 'Weak' if rssi < -70 else \
           'Fair' if rssi < -60 else \
           'Good' if rssi < -50 else \
           'Excellent'

# ------------------------------------------------------------------------------------

def _nameFromAuthCode(authCode) :
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

# ------------------------------------------------------------------------------------

wlan     = network.WLAN(network.STA_IF)
ifActive = wlan.active()

print('Scans for wireless access points...')
if not ifActive :
    wlan.active(True)
scan = wlan.scan()
if not ifActive :
    wlan.active(False)
print()
print('Total access points found = %s' % len(scan))

i = 0
for x in scan :
    ssid     = x[0].decode('UTF-8')
    macaddr  = _macAddrFromBSSID(x[1])
    chan     = x[2]
    rssi     = x[3]
    signal   = _signalStrengthFromRSSI(rssi)
    authName = _nameFromAuthCode(x[4])
    hidden   = x[5]
    i += 1
    print('\n%02d> MAC address (BSSID) : %s' % (i, macaddr))
    if not hidden :
        print('    SSID                : %s' % ssid)
    else :
        print('    SSID (is hidden)    :')
    print('    Channel             : %s' % chan)
    print('    RSSI (signal)       : %s dBm (%s)' % (rssi, signal))
    print('    Authentication type : %s' % authName)
