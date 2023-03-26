
# === START_CONFIG_PARAMETERS ===

dict(
    
    info = dict(
        name        = '1-Wire Devices Scan',
        version     = [1, 0, 0],
        description = 'Initializes a 1-Wire bus on a single GPIO and finds all the family IDs and serial numbers of slave devices.',
        author      = 'JC`zic',
        mail        = 'jczic.bos@gmail.com',
        www         = 'https://github.com/jczic'
    ),
    
    args = dict(

        dataPin  = dict( label    = 'Data GPIO:',
                         type     = list )

    )

)

# === END_CONFIG_PARAMETERS ===


from machine import Pin
from onewire import OneWire

try :
    dataPin = Pin(args.dataPin)
    try :
        print('1-Wire initialization...')
        print()
        ow = OneWire(dataPin)
        if ow.reset() :
            try :
                print('Scans the 1-Wire bus...')
                print()
                count = 0
                roms  = ow.scan()
                for rom in roms :
                    if len(rom) == 8 and ow.crc8(rom[:7]) == rom[7] :
                        deviceID = hex(rom[0])
                        deviceSR = rom[1:7].hex()
                        print('  - Device found: [FamilyID=%s] [Serial=%s]' % (deviceID, deviceSR))
                        count += 1
                if count :
                    print()
                    print('%s device(s) found!' % count)
                else :
                    print('No device found.')
            except :
                print('Bus communication error.')
        else :
            raise
    except :
        print('Unable to initialize the bus on GPIO-%s (does the data wire exist?).' % args.dataPin)
except :
    print('GPIO-%s invalid.' % args.dataPin)
