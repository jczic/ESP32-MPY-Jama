
# === START_CONFIG_PARAMETERS ===

dict(

    timeout         = 7,
    
    info = dict(
        name        = 'NTP Time Sync',
        version     = [1, 0, 0],
        description = ''' This tool synchronizes the UTC date and time from an NTP server.
                          You can choose the NTP server host to connect to.
                      ''',
        author      = 'JC`zic',
        mail        = 'jczic.bos@gmail.com',
        www         = 'https://github.com/jczic'
    ),
    
    args = dict(

        ntp_srv = dict( label    = 'NTP server host:',
                        type     = str,
                        value    = 'pool.ntp.org' )
    
    )

)

# === END_CONFIG_PARAMETERS ===


import ntptime
from   time    import gmtime
from   network import WLAN, STA_IF

def _getUTCDateTime() :
    dt = gmtime()
    return (dt if dt[0] >= 2023 else None)

if not args.ntp_srv or args.ntp_srv.find('.') == -1 :
    print('Please, enter a correct NTP server host.')
    import sys
    sys.exit()

wlan = WLAN(STA_IF)
if not wlan.active() or wlan.ifconfig()[0] == '0.0.0.0' :
    print('Please, connect your ESP32 to a Wi-Fi access point first.')
    import sys
    sys.exit()

ntptime.host = args.ntp_srv

try :
    ntptime.settime()
except Exception as ex :
    print('Unable to connect to NTP server "%s" (%s).' % (ntptime.host, ex))
    import sys
    sys.exit()

dt = _getUTCDateTime()
if dt :
    print('Ok synchronized, UTC date/time:\n>> %4d-%02d-%02d %02d:%02d:%02d' % (dt[0], dt[1], dt[2], dt[3], dt[4], dt[5]))
else :
    print('Error in synchronizing the current UTC date/time.')
