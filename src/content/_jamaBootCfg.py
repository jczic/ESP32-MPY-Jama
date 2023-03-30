
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

        def gInt(key, noneOk=False) :
            try :
                return nvs.get_i32(key)
            except :
                if not noneOk :
                    raise

        # MCU,
        try :
            mcuFreq = gInt('mcufreq')
            print('Sets the MCU frequency to %s MHz...' % mcuFreq, end=' ')
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
            print('Initiates Wi-Fi connection to %s...' % ssid, end=' ')
            try :
                import network
                wl = network.WLAN(network.STA_IF)
                wl.active(False)
                wl.active(True)
                wl.connect(ssid, key)
                print('OK')
                print('  - Connecting...')
            except :
                print('ERROR')
        except :
            pass

        # WLAN AP,
        try :
            ssid   = gStr('apssid')
            auth   = gInt('apauth')
            key    = gStr('apkey')
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
            print('  - Initialization...', end=' ')
            try :
                lan = network.LAN( mdc      = machine.Pin(mdcPinNum),
                                   mdio     = machine.Pin(mdioPinNum),
                                   power    = machine.Pin(powerPinNum) \
                                              if powerPinNum is not None else None,
                                   phy_type = network.__dict__['PHY_%s' % driverName],
                                   phy_addr = phyAddr )
                print('OK')
                print('  - Activation...', end=' ')
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
            print('  - Initialization...', end=' ')
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
                    print('NOT PRESENT')
            except :
                print('NOT SUPPORTED')
        except :
            pass

    except :
        pass

config()
del config
