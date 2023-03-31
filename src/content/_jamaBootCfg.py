
___jama = dict()

def config() :

    try :

        from esp32 import NVS
        nvs = NVS('esp32Ctrl')
        buf = bytearray(256)

        def gStr(key, noneOk=False) :
            try :
                sz = nvs.get_blob(key, buf)
                return buf[:sz].decode()
            except :
                if not noneOk :
                    raise
            return None

        def gInt(key, noneOk=False) :
            try :
                return nvs.get_i32(key)
            except :
                if not noneOk :
                    raise
            return None

        # MCU,
        try :
            mcuFreq = gInt('mcufreq')
            print('Setting the MCU frequency to %s MHz...' % mcuFreq, end=' ')
            try :
                from machine import freq
                freq(mcuFreq * 1000000)
                print('OK')
            except :
                print('ERROR')
        except :
            pass

        # WLAN STA,
        try :
            ssid = gStr('ssid')
            key  = gStr('key')
            print('Connecting Wi-Fi to "%s"...' % ssid, end=' ')
            try :
                import network, time
                wl = network.WLAN(network.STA_IF)
                wl.active(False)
                wl.active(True)
                wl.config(reconnects=2)
                wl.connect(ssid, key)
                t = time.ticks_ms()
                while ( time.ticks_diff(time.ticks_ms(), t) <= 15*1000 and \
                        wl.status() == network.STAT_CONNECTING ) :
                    time.sleep(0.100)
                if wl.isconnected() :
                    wl.config(reconnects=-1)
                    print('OK')
                else :
                    if wl.status() == network.STAT_CONNECTING :
                        print('TIMEOUT') # 15s
                    else :
                        print('FAILED')
                    wl.active(False)
            except :
                print('ERROR')
        except :
            pass

        # WLAN AP,
        try :
            ssid   = gStr('apssid')
            auth   = gInt('apauth')
            key    = gStr('apkey', True)
            maxCli = gInt('apmaxcli')
            print('Opening Wi-Fi AP "%s"...' % ssid, end=' ')
            try :
                import network
                wl = network.WLAN(network.AP_IF)
                wl.active(True)
                try :
                    wl.config(ssid=ssid, authmode=auth, password=key)
                except :
                    wl.config(essid=ssid, authmode=auth, password=key)
                wl.config(max_clients=maxCli)
                print('OK')
            except :
                print('ERROR')
        except :
            pass

        # ETH,
        try :
            driverName  = gStr('ethdriver')
            phyAddr     = gInt('ethaddr')
            mdcPinNum   = gInt('ethmdc')
            mdioPinNum  = gInt('ethmdio')
            powerPinNum = gInt('ethpower', True)
            print('Ethernet PHY interface:')
            import network, machine
            print('  - Initializing...', end=' ')
            try :
                lan = network.LAN( mdc      = machine.Pin(mdcPinNum),
                                   mdio     = machine.Pin(mdioPinNum),
                                   power    = machine.Pin(powerPinNum) \
                                              if powerPinNum is not None else None,
                                   phy_type = network.__dict__['PHY_%s' % driverName],
                                   phy_addr = phyAddr )
                print('OK')
                print('  - Activating...', end=' ')
                try :
                    lan.active(True)
                    print('OK')
                except :
                    print('ERROR')
            except :
                print('ERROR')
        except :
            pass

        # SD,
        try :
            mountPt = gStr('sdmountpt')
            print('SD card file system:')
            print('  - Initializing...', end=' ')
            try :
                from machine import SDCard
                try :
                    sd = SDCard()
                    sd.info()[0]
                    print('OK')
                    ___jama["sdCard"] = sd
                    print('  - Mounting on "%s"...' % mountPt, end=' ')
                    try :
                        from uos import mount
                        mount(sd, mountPt)
                        ___jama["sdMountPt"] = mountPt
                        print('OK')
                    except :
                        print('ERROR')
                except :
                    print('NO SD CARD')
            except :
                print('NOT SUPPORTED')
        except :
            pass

    except :
        pass

config()
del config
