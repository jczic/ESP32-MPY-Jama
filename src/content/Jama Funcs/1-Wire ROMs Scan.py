
# === START_CONFIG_PARAMETERS ===

dict(
    
    info = dict(
        name        = '1-Wire ROMs Scan',
        version     = [1, 0, 0],
        description = 'Initializes a 1-Wire bus on a single data GPIO and scans it to find all the ROM (addresses).',
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
                roms = ow.scan()
                if roms :
                    for rom in roms :
                        print('  - ROM found: [%s]' % rom.hex())
                    print()
                    print('%s ROM(s)!' % len(roms))
                else :
                    print('No ROM found.')
            except :
                print('Bus communication error.')
        else :
            print('Unable to reset the bus on GPIO-%s (does the data wire exist?).' % args.dataPin)
    except Exception as ex :
        print('Bus initialization error (%s).' % ex)
except :
    print('GPIO-%s invalid.' % args.dataPin)
